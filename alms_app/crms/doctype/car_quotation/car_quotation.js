
function send_email(user, email_send_to, payload = null) {
    console.log(user);
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name: user,
            email_send_to: email_send_to,
            payload: payload,
        },
        callback: function (response) {
            if (!response.exc) {
                console.log("Mail gya ki nhi")
                frappe.msgprint("Email successful!");
            } else {
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
function uploadfile(frm) {
    if (frm.doc.finance_team_status !== "Approved") {

        frm.add_custom_button('Upload File', function () {
            frappe.prompt(
                {
                    label: 'Upload File',
                    fieldname: 'file',
                    fieldtype: 'Attach',
                    reqd: 1
                },
                function (values) {
                    frappe.call({
                        method: 'alms_app.crms.doctype.car_quotation.car_quotation.process_uploaded_file',
                        args: {
                            file_url: values.file,
                        },
                        callback: function (response) {
                            if (response.message) {
                                setValuesInField(frm, response.message.car_quotation_item);
                            }
                        },
                        error: function () {
                            frappe.msgprint({
                                title: __('Error'),
                                message: __('An error occurred while processing the file.'),
                                indicator: 'red',
                            });
                        },
                    });
                },
                __('Upload File'),
                __('Process')
            );
        }, 'Request Menu')

        // Sub-button for sending email
        // frm.add_custom_button('Send Modification Quot Email', function () {
        //     frappe.msgprint(__('Email sent successfully!'));
        //     frm.set_value("revised_modified_quotation_id",frm.name);
        //     frm.set_value("quotation_status","Modified")
        //     send_email(frm.doc.employee_details, "FinanceHead To Quotation Company", { "email_phase": "New", "email_send_to": frm.doc.finance_company })
        // }, 'Request Menu')

        frm.add_custom_button('Send Revised Quot Email', function () {
            frappe.msgprint(__('Email sent successfully!'));
            frm.set_value("revised_modified_quotation_id", frm.name);
            frm.set_value("quotation_status", "Revised") //here
            frm.refresh_field("revised_modified_quotation_id")
            frm.refresh_field("quotation_status")
            send_email(frm.doc.employee_details, "FinanceHead To Quotation Company", { "email_phase": "Revised", "email_send_to": frm.doc.finance_company })
        }, 'Request Menu')
    }
}

function setValuesInField(frm, data) {

    const ListOfColumns = [
        "finance_company", "accessory", "gst_and_cess",
        "employee_details", "discount_excluding_gst", "insurance",
        "location", "base_price_less_discounts", "fleet_management_repairs_and_tyres",
        "kms", "total_discount", "24x7_assist",
        "variant", "ex_showroom_amount_net_of_discount", "pickup_and_drop",
        "quote", "registration_charges", "pickup_and_drop",
        "interest_rate", "residual_value_percent", "std_relief_car_non_accdt",
        "tenure", "financed_amount", "gst_on_fms",
        "base_price_excluding_gst", "financed_amount", "total_emi",
        "gst", "emi_financing", "status",
        "ex_showroom_amount", "finance_emi_road_tax"
    ]

    ListOfColumns.forEach(column => {
        if (data[column] !== undefined) {
            frm.set_value(column, data[column]);
        } else {
            frappe.msgprint(`${column} not found in data`);
        }
    })
}

let by_button = false
function updateStatus(frm) {
    // frm.clear_custom_buttons();
    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: {
            current_frappe_user: frappe.session.user
        },
        callback: function (r) {
            const userData = r.message;
            console.log("User Data", userData, "+++++++++++++++++++++++++++++")
            if (!userData) return;

            const alloweddesignations = ["Finance", "Administrator"];

            if (alloweddesignations.includes(userData)) {
                uploadfile(frm);
            }

            const allowedDesignations = ["Finance", "Finance Head", "Administrator"];

            if (allowedDesignations.includes(userData)) {
                // frm.clear_custom_buttons();
                const buttons = [
                    {
                        label: "Finance Team",
                        field: "status",
                        current_status: frm.doc.finance_team_status,
                        designation_match: "Finance",
                        btn_field: "finance_team_status"
                    },
                    {
                        label: "Finance Head",
                        field: "status",
                        current_status: frm.doc.finance_head_status,
                        designation_match: "Finance Head",
                        btn_field: "finance_head_status"
                    },
                ];
                buttons.forEach(button => {
                    const status = button.current_status || "Pending";
                    let status_color;

                    switch (status) {
                        case "Approved":
                            status_color = "darkgreen";
                            break;
                        case "Rejected":
                            status_color = "darkred";
                            break;
                        default:
                            status_color = "gray";
                    }

                    const btn = frm.add_custom_button(`${button.label}: ${status}`, () => {
                        if (status === "Pending" && (userData === button.designation_match || userData === "Administrator")) {
                            console.log("here");
                            if (button.btn_field !== "finance_team_status" && frm.doc.finance_team_status !== "Approved") {
                                frappe.msgprint("Finance Team must approve before further approvals.");
                                return;
                            }

                            frappe.prompt([
                                {
                                    fieldname: 'remarks_input',
                                    label: `Enter ${button.label} Remarks`,
                                    fieldtype: 'Data',
                                    reqd: 1
                                }
                            ],
                                function (values) {
                                    if (button.btn_field === "finance_team_status") {
                                        frm.set_value("finance_team_remarks", values.remarks_input);
                                    }
                                    if (button.btn_field === "finance_head_status") {
                                        frm.set_value("finance_head_remarks", values.remarks_input);
                                    }

                                    frm.set_value(button.btn_field, "Approved");
                                    frm.refresh_field(button.btn_field);
                                    frm.save().then(() => {
                                        if (button.btn_field === "finance_team_status") {
                                            send_email(frm.doc.employee_details, "FinanceTeam To FinanceHead")
                                        }
                                        if (button.btn_field === "finance_head_status") {
                                            send_email(frm.doc.employee_details, "FinanceHead To AccountsTeam", { "quotation_id": frm.doc.name })
                                        }
                                        updateStatus(frm);

                                    });
                                },
                                'Remarks Required',
                                'Submit');
                        }
                        by_button = true;
                    });
                    btn.css({
                        "background-color": status_color,
                        "color": "white",
                        "border-color": status_color,
                        "cursor": (status === "Pending" && (userData === button.designation_match || userData === "Administrator")) ? "pointer" : "not-allowed"
                    });

                    // Disable button click if not allowed
                    if (!(status === "Pending" && (userData === button.designation_match || userData === "Administrator"))) {
                        btn.off("click");
                    }
                });
            }
        }
    })
}

function FinalSelectedQuotation(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: frm.doc.doctype,
            fields: ['name'],
            filters: {
                'employee_details': frm.doc.employee_details,
            },
            limit_page_length: 100
        },
        callback: function (response) {
            if (response.message && response.message.length > 0) {
                let rejectedDocs = response.message
                    .map(doc => doc.name)
                    .filter(name => name !== frm.doc.name);
                // alert("Rejected Quotations: \n" + rejectedDocs.join("\n"));
                rejectedDocs.forEach(docName => {
                    frappe.call({
                        method: 'frappe.client.set_value',
                        args: {
                            doctype: frm.doc.doctype,
                            name: docName,
                            fieldname: {
                                status: 'Rejected',
                                finance_head_status: 'Rejected',
                                finance_team_status: 'Rejected'
                            },
                        },
                        callback: function (res) {
                            if (!res.exc) {
                                console.log(`Updated ${docName} to Rejected`);
                            } else {
                                console.log(`Failed to update ${docName}`);
                            }
                        }
                    });
                });
            } else {
                frappe.msgprint(__('No Pending Quotations found.'));
            }
        }
    });
    frm.set_value("status", "Approved");
    frm.save();
    // frappe.msgprint(__('Current quotation approved, others rejected.'));
}


function toggleFieldStatus(frm) {

    Object.keys(frm.fields_dict).forEach(function (fieldname) {
        frappe.call({
            method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
            args: {
                current_frappe_user: frappe.session.user
            },
            callback: function (r) {
                const userData = r.message;
                if (userData === "Finance Head" && fieldname === "finance_head_status") {
                    frm.set_df_property(fieldname, "read_only", 0);
                } else if (userData === "Finance" && fieldname === "finance_team_status") {
                    frm.set_df_property(fieldname, "read_only", 0);
                } else if (userData === "Administrator" && (fieldname === "finance_head_status" || fieldname === "finance_team_status")) {
                    frm.set_df_property(fieldname, "read_only", 0);
                } else if (userData === "Administrator") {
                    frm.set_df_property(fieldname, "read_only", 0);
                } else {
                    frm.set_df_property(fieldname, "read_only", 1);
                }

            }
        })

    });
}

frappe.ui.form.on('Car Quotation', {
    refresh: function (frm) {
        frm.set_df_property("status", "read_only", true);
        // frm.set_df_property('status', 'read_only', 1);
        updateStatus(frm);
        console.log("hello ha  bhai ++++++")
        toggleFieldStatus(frm);
        uploadfile(frm);

    },
    onload: function (frm) {
        frm.set_df_property("status", "read_only", true);
        updateStatus(frm);
        toggleFieldStatus(frm);
        uploadfile(frm);

    },

    finance_head_status: function (frm) {
        if (by_button === true) {
            frm.set_value("status", "Approved");
            by_button = false;
            frm.save_or_update();
            return;
        }

        if (frm.doc.finance_head_status !== "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value('finance_head_remarks', values.remarks_input);
                    console.log("finance status:", frm.doc.finance_head_status)
                    frm.refresh_field('finance_head_remarks');
                    frm.save().then(() => {
                        if (frm.doc.finance_head_status === "Approved") {
                            frm.set_value("status", "Approved");
                        }
                        else if (frm.doc.finance_head_status === "Rejected") {
                            frm.set_value("status", "Rejected");
                        }
                        frm.save_or_update();
                        if (frm.doc.finance_head_status === "Approved") {
                            send_email(frm.doc.employee_details, "FinanceHead To AccountsTeam", { "quotation_id": frm.doc.name })
                        }
                        else if (frm.doc.finance_head_status === "Rejected") {
                            send_email(frm.doc.employee_details, "Reject FinanceHead to Vendor", { "quotation_id": frm.doc.name })

                        }
                    });

                },
                'Remarks Required',
                'Submit');
        }
        else {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value('finance_head_remarks', values.remarks_input);
                    frm.refresh_field('finance_head_remarks');
                    frm.set_value("status", "Pending");
                    frm.save().then(() => {
                        frm.save_or_update();
                    });

                },
                'Remarks Required',
                'Submit'
            );
            frm.save_or_update();
        }
    },

    finance_team_status: function (frm) {
        if (by_button === true) {
            by_button = false;

            return;
        }
        console.log("inside function")
        if (frm.doc.finance_team_status && frm.doc.finance_team_status !== "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value('finance_team_remarks', values.remarks_input);
                    frm.refresh_field('finance_team_remarks');
                    frm.save().then(() => {
                        if (frm.doc.finance_team_status === "Approved") {
                            send_email(frm.doc.employee_details, "FinanceTeam To FinanceHead")
                        }
                        else if (frm.doc.finance_team_status === "Rejected") {
                            console.log("rejected")
                            send_email(frm.doc.employee_details, "Reject FinanceTeam to Vendor", { "quotation_id": frm.doc.name })

                        }
                    });
                },
                'Remarks Required',
                'Submit'
            );

        } else {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value('finance_team_remarks', values.remarks_input);
                    frm.refresh_field('finance_team_remarks');
                    frm.save().then(() => {
                        frm.save_or_update();
                    });

                },
                'Remarks Required',
                'Submit'
            );
            frm.save_or_update();
        }
    },

});