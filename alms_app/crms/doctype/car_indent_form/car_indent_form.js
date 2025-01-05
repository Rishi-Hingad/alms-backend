function changeStatus(frm, field_to_update, new_status) {
    frm.set_value(field_to_update, new_status); // Update the specified field with the new status

    frm.save()
        .then(function () {
            frm.refresh_field(field_to_update); // Refresh the updated field
            frm.clear_custom_buttons(); // Clear buttons
            updateStatus(frm); // Refresh buttons based on the new status
            if (field_to_update === "status_head" && new_status === "Approved") {
                onApprovalByHRHead();
            }

        })
        .catch(function (error) {
            frappe.msgprint(__('Error saving document: ') + error.message); // Display error if save fails
        });
}


function onApprovalByHRHead() {
    // Function called when HR Head approves
    frappe.msgprint(__('Successfully approved this request'));
}

function updateStatus(frm) {
    frm.clear_custom_buttons(); // Remove existing buttons

    // Fetch the user's designation
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "User",
            name: frappe.session.user, // Current logged-in user
        },
        callback: function (response) {
            if (response && response.message) {
                const designation = response.message.designation;

                // Define buttons for each designation
                const buttons = [
                    {
                        label: "Reporting Head Action",
                        field: "reporting_head_approval",
                        current_status: frm.doc.reporting_head_approval,
                        designation: "Reporting Head",
                        enabled: designation === "Reporting Head"
                    },
                    {
                        label: "HR Action",
                        field: "hr_approval",
                        current_status: frm.doc.hr_approval,
                        designation: "HR",
                        enabled: designation === "HR"
                    },
                    {
                        label: "HR Head Action",
                        field: "hr_head_approval",
                        current_status: frm.doc.hr_head_approval,
                        designation: "HR Head",
                        enabled: designation === "HR Head"
                    }
                ];

                // Add buttons
                buttons.forEach(button => {
                    if (button.current_status === "Pending" && button.enabled) {
                        frm.add_custom_button(button.label, function () {
                            // Show a dropdown to select Approve or Reject
                            frappe.prompt(
                                {
                                    label: __('Select Action'),
                                    fieldname: 'action',
                                    fieldtype: 'Select',
                                    options: ['Approved', 'Rejected'], // Dropdown options
                                    reqd: 1
                                },
                                function (data) {
                                    // Update the status based on user selection
                                    frm.set_value(button.field, data.action);
                                    frm.save_or_update().then(() => {
                                        frappe.msgprint(
                                            __('Status for {0} changed to {1}.', [button.label, data.action])
                                        );
                                        frm.refresh_field(button.field);
                                    });
                                },
                                __('Approval Action'),
                                __('Submit')
                            );
                        });
                    } else {
                        // Add a non-interactive button to show the current status
                        const status_color =
                            button.current_status === "Approved"
                                ? "darkgreen"
                                : button.current_status === "Rejected"
                                ? "darkred"
                                : "lightgray";

                        frm.add_custom_button(`${button.label}: ${button.current_status}`, null).css({
                            "background-color": status_color,
                            "color": "white",
                            "border-color": status_color,
                            "cursor": "not-allowed"
                        });
                    }
                });
            }
        }
    });
}


frappe.ui.form.on("Car Indent Form", {
    onload: function(frm) {
        // Set fields to read-only on load
        frm.set_df_property('employee_code', 'read_only', 1);
        frm.set_df_property('ex_showroom_price', 'read_only', 1);
        frm.set_df_property('discount', 'read_only', 1);
        frm.set_df_property('tcs', 'read_only', 1);
        frm.set_df_property('registration_charges', 'read_only', 1);
        frm.set_df_property('accessories', 'read_only', 1);
        frm.set_df_property('make', 'read_only', 1);
        frm.set_df_property('engine', 'read_only', 1);
        frm.set_df_property('colour', 'read_only', 1);
        // frm.set_df_property('status', 'read_only', 1);
        // frm.set_df_property('reporting_head_approval', 'read_only', 1);
        // frm.set_df_property('status_head', 'read_only', 1);
        frm.set_df_property('model', 'read_only', 1);
        // frm.set_df_property('quotation_document', 'read_only', 1);
    },

    status: function(frm) {
        // Call the updateStatus function when the status changes
        updateStatus(frm);
    },

    refresh(frm) {
        // Recalculate totals and update the status button on refresh
        calculate_totals(frm);
        updateStatus(frm);
    },

    ex_showroom_price: function(frm) {
        calculate_totals(frm);
    },

    discount: function(frm) {
        calculate_totals(frm);
    },

    tcs: function(frm) {
        calculate_totals(frm);
    },

    registration_charges: function(frm) {
        calculate_totals(frm);
    },

    accessories: function(frm) {
        calculate_totals(frm);
    }
});

function calculate_totals(frm) {
    const ex_showroom_price = frm.doc.ex_showroom_price || 0;
    const discount = frm.doc.discount || 0;
    const tcs = frm.doc.tcs || 0;
    const registration_charges = frm.doc.registration_charges || 0;
    const accessories = frm.doc.accessories || 0;

    // Calculate net showroom price and finance amount
    frm.set_value("net_ex_showroom_price", ex_showroom_price - discount + tcs);

    const finance_amount = (ex_showroom_price - discount + tcs) + registration_charges + accessories;
    frm.set_value("finance_amount", finance_amount);
}
