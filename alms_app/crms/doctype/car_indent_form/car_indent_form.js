function send_email(user, email_send_to) {
    console.log("send_email called with:", user, email_send_to);
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name: user,
            email_send_to: email_send_to,
        },
        callback: function (response) {
            if (response.exc) {
                frappe.msgprint({
                    title: "Error",
                    indicator: "red",
                    message: response.exc || "An unknown error occurred while sending the email.",
                });
            }
        },
        error: function (error) {
            frappe.msgprint({
                title: "Error",
                indicator: "red",
                message: error.message || "An unknown error occurred while sending the email.",
            });
        },
    });
}

let by_button = false;

function updateStatus(frm) {
    frm.clear_custom_buttons();

    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: { current_frappe_user: frappe.session.user },
        callback: function (r) {
            const designation = r.message;
            console.log("User Designation:", designation);

            const stages = [
                { label: "Reporting Head", field: "reporting_head_approval", remarks_field: "reporting_head_remarks", status: frm.doc.reporting_head_approval },
                { label: "HR", field: "hr_approval", remarks_field: "hr_remarks", status: frm.doc.hr_approval },
                { label: "HR Head", field: "hr_head_approval", remarks_field: "hr_head_remarks", status: frm.doc.hr_head_approval }
            ];

            const visibilityMap = {
                "Reporting Head": ["reporting_head_approval"],
                "HR": ["reporting_head_approval", "hr_approval"],
                "HR Head": ["reporting_head_approval", "hr_approval", "hr_head_approval"],
                "Administrator": stages.map(s => s.field)
            };

            const editableMap = {
                "Reporting Head": ["reporting_head_approval"],
                "HR": ["hr_approval"],
                "HR Head": ["hr_head_approval"],
                "Administrator": stages.map(s => s.field)
            };

            const visibleFields = visibilityMap[designation] || [];
            const editableFields = editableMap[designation] || [];

            stages.forEach(stage => {
                const status = stage.status || "Pending";
                const color = {
                    "Approved": "darkgreen",
                    "Rejected": "darkred",
                    "Pending": "gray"
                }[status] || "gray";

                if (visibleFields.includes(stage.field)) {
                    const canEdit = editableFields.includes(stage.field);

                    const btn = frm.add_custom_button(`${stage.label}: ${status}`, () => {
                        if (!canEdit) {
                            frappe.msgprint(`You can only view the status of ${stage.label}.`);
                            return;
                        }

                        if (stage.field === "hr_approval" && frm.doc.reporting_head_approval !== "Approved") {
                            frappe.msgprint("Reporting Head must approve first.");
                            return;
                        }
                        if (stage.field === "hr_head_approval" && frm.doc.hr_approval !== "Approved") {
                            frappe.msgprint("HR must approve first.");
                            return;
                        }

                        frappe.prompt([
                            {
                                fieldname: 'action_choice',
                                label: `Action for ${stage.label}`,
                                fieldtype: 'Select',
                                options: ['Approved', 'Rejected'],
                                reqd: 1
                            },
                            {
                                fieldname: 'remarks_input',
                                label: `Enter ${stage.label} Remarks`,
                                fieldtype: 'Data',
                                reqd: 1
                            }
                        ],
                            function (values) {
                                frm.set_value(stage.remarks_field, values.remarks_input);
                                frm.set_value(stage.field, values.action_choice);

                                if (stage.field === "hr_head_approval") {
                                    frm.set_value("status", values.action_choice);
                                }

                                frm.save().then(() => {
                                    const emailMap = {
                                        "Approved": {
                                            "reporting_head_approval": "ReportingHead To HR",
                                            "hr_approval": "HR To HRHead",
                                            "hr_head_approval": "HRHead To PurchaseTeam"
                                        },
                                        "Rejected": {
                                            "reporting_head_approval": "Reject Reporting to Employee",
                                            "hr_approval": "Reject HRTeam to Employee",
                                            "hr_head_approval": "Reject HRHead to Employee"
                                        }
                                    };

                                    send_email(frm.doc.name, emailMap[values.action_choice][stage.field]);
                                    updateStatus(frm);
                                });
                            },
                            'Action Required',
                            'Submit'
                        );
                        by_button = true;
                    });

                    btn.css({
                        "background-color": color,
                        "color": "white",
                        "border-color": color,
                        "cursor": canEdit ? "pointer" : "not-allowed",
                        "opacity": canEdit ? "1" : "0.6"
                    });

                    if (!canEdit) btn.off("click");
                }
            });
        }
    });
}

function toggleFieldStatus(frm) {
    const fieldMap = {
        "Reporting Head": "reporting_head_approval",
        "HR": "hr_approval",
        "HR Head": "hr_head_approval"
    };

    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: { current_frappe_user: frappe.session.user },
        callback: function (r) {
            const designation = r.message;

            if (designation && fieldMap[designation]) {
                frm.set_df_property(fieldMap[designation], "read_only", 0);
            }
            if (frappe.session.user === "Administrator") {
                Object.values(fieldMap).forEach(field => {
                    frm.set_df_property(field, "read_only", 0);
                });
            }

            if (
                (designation === "Purchase" || designation === "Purchase Head" || designation === "Administrator") &&
                frm.doc.reporting_head_approval === "Approved" &&
                frm.doc.hr_approval === "Approved" &&
                frm.doc.hr_head_approval === "Approved"
            ) {
                let employeeName = frm.doc.employee_name || frm.doc.employee_code;
                if (!employeeName) {
                    frappe.msgprint("No employee name/code found. Skipping purchase form check.");
                    return;
                }

                frappe.call({
                    method: "alms_app.crms.doctype.car_indent_form.car_indent_form.check_purchase_form_exists",
                    args: {
                        employee_name: employeeName
                    },
                    callback: function (res) {
                        if (res.message) {
                            console.log("Purchase Form already exists. Button hidden.");
                            return;
                        }

                        frm.add_custom_button(__('Redirect to Purchase Form'), function () {
                            let apiUrl = `${window.location.origin}/app/purchase-team-form/new-purchase-team-form-?employee_name=${encodeURIComponent(employeeName)}`;
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
        frm.set_df_property('reporting_head_approval', 'read_only', 1);
        frm.set_df_property('hr_approval', 'read_only', 1);
        frm.set_df_property('hr_head_approval', 'read_only', 1);
        frm.set_df_property('status', 'read_only', 1);
        frm.set_df_property('model', 'read_only', 1);
        frm.set_df_property('reporting_head_remarks', 'read_only', 1);
        frm.set_df_property('hr_head_remarks', 'read_only', 1);
        frm.set_df_property('hr_remarks', 'read_only', 1);
        frm.set_df_property('default_currency', 'read_only', 1);
        frm.set_df_property('form_type', 'read_only', 1);
        toggleFieldStatus(frm);
        check_user_access(frm);
    },

    refresh: function (frm) {
        updateStatus(frm);
        toggleFieldStatus(frm);

        // Add custom button to call both APIs
        frm.add_custom_button(__('Check & Send Email'), function () {
            checkAndSendEmail(frm);
        }).css({
            "background-color": "darkgreen",
            "color": "white",
            "border": "none",
            "padding": "8px 15px",
            "font-size": "13px",
            "border-radius": "5px",
            "cursor": "pointer"
        });
        check_user_access(frm);

    },

    reporting_head_approval: function (frm) {
        if (by_button) { by_button = false; return; }
        if (frm.doc.reporting_head_approval && frm.doc.reporting_head_approval !== "Pending") {
            frappe.prompt([{ fieldname: 'remarks_input', label: 'Enter Remarks', fieldtype: 'Data', reqd: 1 }],
                function (values) {
                    frm.set_value("reporting_head_remarks", values.remarks_input);
                    frm.refresh_field("reporting_head_remarks");
                    frm.save().then(() => {
                        if (frm.doc.reporting_head_approval === "Approved")
                            send_email(frm.doc.name, "ReportingHead To HR");
                        else if (frm.doc.reporting_head_approval === "Rejected")
                            send_email(frm.doc.name, "Reject Reporting to Employee");
                    });
                }, 'Remarks Required', 'Submit');
        }
    },

    hr_approval: function (frm) {
        if (by_button) { by_button = false; return; }
        if (frm.doc.reporting_head_approval !== "Approved") {
            frappe.msgprint("Reporting Head must approve before HR!");
            return;
        }
        if (frm.doc.hr_approval && frm.doc.hr_approval !== "Pending") {
            frappe.prompt([{ fieldname: 'remarks_input', label: 'Enter Remarks', fieldtype: 'Data', reqd: 1 }],
                function (values) {
                    frm.set_value("hr_remarks", values.remarks_input);
                    frm.refresh_field("hr_remarks");
                    frm.save().then(() => {
                        if (frm.doc.hr_approval === "Approved")
                            send_email(frm.doc.name, "HR To HRHead");
                        else if (frm.doc.hr_approval === "Rejected")
                            send_email(frm.doc.name, "Reject HRTeam to Employee");
                    });
                }, 'Remarks Required', 'Submit');
        }
    },

    hr_head_approval: function (frm) {
        if (by_button) { by_button = false; return; }
        if (frm.doc.reporting_head_approval !== "Approved" || frm.doc.hr_approval !== "Approved") {
            frappe.msgprint("Reporting Head and HR must approve before HR Head!");
            return;
        }
        if (frm.doc.hr_head_approval && frm.doc.hr_head_approval !== "Pending") {
            frappe.prompt([{ fieldname: 'remarks_input', label: 'Enter Remarks', fieldtype: 'Data', reqd: 1 }],
                function (values) {
                    frm.set_value("hr_head_remarks", values.remarks_input);
                    frm.refresh_field("hr_head_remarks");
                    frm.save().then(() => {
                        if (frm.doc.hr_head_approval === "Approved") {
                            frm.set_value("status", "Approved");
                            send_email(frm.doc.name, "HRHead To PurchaseTeam");
                        } else if (frm.doc.hr_head_approval === "Rejected") {
                            frm.set_value("status", "Rejected");
                            send_email(frm.doc.name, "Reject HRHead to Employee");
                        }
                        frm.refresh_field("status");
                    });
                }, 'Remarks Required', 'Submit');
        }
    }
});

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

function checkAndSendEmail(frm) {
    const employeeCode = frm.doc.employee_code;
    console.log(employeeCode)

    frappe.call({
        method: "alms_app.crms.web_form.car_indent_form.car_indent_form.send_email_to_reporting_head_dcotype",
        args: { doc: employeeCode },
        callback: function () {
            frappe.msgprint("Email sent to Reporting Head!");
        },
        error: function () {
            frappe.throw("Error sending car indent email.");
        }

    });
    console.log("API method for send mail to repoarting head is successfully called!!!!!!!!!!!")
}

frappe.ui.form.on("Car Indent Form", {
    refresh: function (frm) {
        if (frappe.session.user !== "Administrator") {
            frm.set_df_property("approval_token", "hidden", 1);
        } else {
            frm.set_df_property("approval_token", "hidden", 0);
        }
    }
});