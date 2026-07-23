function renderPurchaseRedirectButton(frm) {
    // Only administrators or Purchase team should see the redirect button
    const is_purchase = frappe.user_roles.includes("Purchase Team") || frappe.user_roles.includes("Purchase Manager") || frappe.user_roles.includes("Purchase Head") || frappe.user_roles.includes("Administrator");
    if (
        is_purchase &&
        frm.doc.status === "Approved"
    ) {
        let employeeCode = frm.doc.employee_code;
        if (!employeeCode) {
            return;
        }

        frappe.call({
            method: "alms_app.crms.doctype.car_indent_form.car_indent_form.check_purchase_form_exists",
            args: {
                employee_code: employeeCode
            },
            callback: function (res) {
                if (res.message) {
                    console.log("Purchase Form already exists. Button hidden.");
                    return;
                }

                frm.add_custom_button(__('Redirect to Purchase Form'), function () {
                    let apiUrl = `${window.location.origin}/app/purchase-form/new-purchase-form-?employee_name=${encodeURIComponent(employeeCode)}`;
                    if (frm.doc.quotation_document) {
                        apiUrl += `&quotation_document=${encodeURIComponent(frm.doc.quotation_document)}`;
                    }
                    window.location.href = apiUrl;
                }).css({
                    'background-color': '#007bff',
                    'color': 'white',
                    'border': 'none',
                    'padding': '10px 20px',
                    'font-size': '14px',
                    'border-radius': '5px',
                    'cursor': 'pointer'
                });
            }
        });
    }
}

function check_user_access(frm) {
    frappe.call({
        method: 'alms_app.crms.doctype.car_indent_form.car_indent_form.can_view_car_indent_list',
        async: false,
        callback: function (r) {
            if (!r.message) {
                frappe.msgprint({
                    title: __('Access Denied'),
                    indicator: 'red',
                    message: __('You do not have the required role to access this document.')
                });

                setTimeout(function () {
                    frappe.set_route('');
                }, 300);
            }
        }
    });
}

frappe.ui.form.on("Car Indent Form", {
    onload: function (frm) {
        frm.set_df_property('employee_code', 'read_only', 1);
        frm.set_df_property('ex_showroom_price', 'read_only', 1);
        frm.set_df_property('discount', 'read_only', 1);
        frm.set_df_property('tcs', 'read_only', 1);
        frm.set_df_property('registration_charges', 'read_only', 1);
        frm.set_df_property('accessories', 'read_only', 1);
        frm.set_df_property('make', 'read_only', 1);
        frm.set_df_property('engine', 'read_only', 1);
        frm.set_df_property('colour', 'read_only', 1);
        frm.set_df_property('model', 'read_only', 1);
        frm.set_df_property('default_currency', 'read_only', 1);
        frm.set_df_property('form_type', 'read_only', 1);

        // Make legacy approval fields read-only for everyone
        let legacy_fields = [
            'reporting_head_approval', 'reporting_head_remarks',
            'hr_approval', 'hr_remarks',
            'travel_desk_approval', 'travel_desk_remarks',
            'hr_head_approval', 'hr_head_remarks'
        ];
        legacy_fields.forEach(f => frm.set_df_property(f, 'read_only', 1));

        if (frappe.session.user === "Administrator") {
            frm.toggle_display(['is_submitted', 'approval_initiated', 'approval_entry', 'approval_trail_html'], true);
        } else {
            frm.set_df_property('status', 'read_only', 1);
        }
        check_user_access(frm);
    },

    refresh: function (frm) {
        if (frm.doc.status === 'Approved') {
            frm.set_df_property('eligibility', 'read_only', 1);
        }

        renderPurchaseRedirectButton(frm);
        check_user_access(frm);
        if (window.setup_approval_ui) {
            window.setup_approval_ui(frm);
        }

        // Add Force Delete Button for Administrator only
        if (frappe.session.user === "Administrator" && !frm.is_new()) {
            frm.add_custom_button(__('Force Delete'), function () {
                frappe.confirm(
                    __('Are you sure you want to permanently delete this form and all its associated Approval Entries? This cannot be undone.'),
                    function () {
                        frappe.call({
                            method: "alms_app.crms.doctype.car_indent_form.car_indent_form.force_delete",
                            args: {
                                docname: frm.doc.name
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint({
                                        title: __('Success'),
                                        message: __('Car Indent Form and its Approval Entries have been deleted.'),
                                        indicator: 'green'
                                    });
                                    setTimeout(() => {
                                        frappe.set_route('List', 'Car Indent Form');
                                    }, 1500);
                                }
                            }
                        });
                    }
                );
            }).css({
                'background-color': '#dc3545',
                'color': 'white'
            });
        }
    }
});