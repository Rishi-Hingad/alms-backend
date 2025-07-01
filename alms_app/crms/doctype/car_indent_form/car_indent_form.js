
function send_email(user, email_send_to) {
    console.log("send_email called with:", user, email_send_to);
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name: user,
            email_send_to: email_send_to,
        },
        callback: function (response) {
            if (!response.exc) {
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

let by_button = false;

function updateStatus(frm) {
    frm.clear_custom_buttons();

    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: {
            current_frappe_user: frappe.session.user
        },
        callback: function (r) {
            const designation = r.message;
            console.log("User Designation:", designation);

            const stages = [
                { label: "Reporting Head", field: "reporting_head_approval", remarks_field: "reporting_head_remarks", status: frm.doc.reporting_head_approval },
                { label: "HR", field: "hr_approval", remarks_field: "hr_remarks", status: frm.doc.hr_approval },
                { label: "Travel Desk", field: "travel_desk_approval", remarks_field: "travel_desk_remarks", status: frm.doc.travel_desk_approval },
                { label: "HR Head", field: "hr_head_approval", remarks_field: "hr_head_remarks", status: frm.doc.hr_head_approval }
            ];

            const visibilityMap = {
                "Reporting Head": ["reporting_head_approval"],
                "HR": ["reporting_head_approval", "hr_approval"],
                "Travel Desk": ["reporting_head_approval", "hr_approval", "travel_desk_approval"],
                "HR Head": ["reporting_head_approval", "hr_approval", "travel_desk_approval", "hr_head_approval"],
                "Administrator": stages.map(s => s.field)
            };

            const editableMap = {
                "Reporting Head": ["reporting_head_approval"],
                "HR": ["hr_approval"],
                "Travel Desk": ["travel_desk_approval"],
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
                        if (stage.field === "travel_desk_approval" && frm.doc.hr_approval !== "Approved") {
                            frappe.msgprint("HR must approve first.");
                            return;
                        }
                        if (stage.field === "hr_head_approval" && frm.doc.travel_desk_approval !== "Approved") {
                            frappe.msgprint("Travel Desk must approve first.");
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
                                            "hr_approval": "HR To Travel Desk",
                                            "travel_desk_approval": "Travel Desk To HRHead",
                                            "hr_head_approval": "HRHead To PurchaseTeam"
                                        },
                                        "Rejected": {
                                            "reporting_head_approval": "Reject Reporting to Employee",
                                            "hr_approval": "Reject HRTeam to Employee",
                                            "travel_desk_approval": "Reject TravelDesk to Employee",
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

                    if (!canEdit) {
                        btn.off("click");
                    }
                }
            });
        }
    });
}

// let by_button = false;
// function updateStatus(frm) {
//     frm.clear_custom_buttons();

//     frappe.call({
//         method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
//         args: {
//             current_frappe_user: frappe.session.user
//         },
//         callback: function (r) {
//             console.log(frappe.session.user);
//             const designation = r.message;
//             console.log("Car Indent Form Designation", designation)

//             const buttons = [
//                 {
//                     label: "Reporting Head",
//                     field: "reporting_head_approval",
//                     current_status: frm.doc.reporting_head_approval,
//                     designation_match: "Reporting Head",
//                 },
//                 {
//                     label: "HR",
//                     field: "hr_approval",
//                     current_status: frm.doc.hr_approval,
//                     designation_match: "HR"
//                 },
//                 {
//                     label: "Travel Desk",
//                     field: "travel_desk_approval",
//                     current_status: frm.doc.travel_desk_approval,
//                     designation_match: "Travel Desk"
//                 },
//                 {
//                     label: "HR Head",
//                     field: "hr_head_approval",
//                     current_status: frm.doc.hr_head_approval,
//                     designation_match: "HR Head"
//                 }
//             ];

            // buttons.forEach(button => {
            //     const status = button.current_status || "Pending";
            //     let status_color;

            //     switch (status) {
            //         case "Approved":
            //             status_color = "darkgreen";
            //             break;
            //         case "Rejected":
            //             status_color = "darkred";
            //             break;
            //         default:
            //             status_color = "gray";
            //     }

            //     const btn = frm.add_custom_button(`${button.label}: ${status}`, () => {
            //         if (status === "Pending" && (designation === button.designation_match || designation === "Administrator")) {
            //             console.log("here")
            //             // Enforce sequential approval
            //             if (button.field !== 'reporting_head_approval' && frm.doc.reporting_head_approval !== "Approved") {
            //                 frappe.msgprint("Reporting Head must approve before further approvals.");
            //                 return;
            //             }
            //             if (button.field === 'travel_desk_approval' && frm.doc.hr_approval !== "Approved") {

            //                 frappe.msgprint("HR must approve before Travel Desk.");
            //                 return;
            //             }
            //             if (button.field === 'hr_head_approval' && frm.doc.travel_desk_approval !== "Approved") {
            //                 frappe.msgprint("Travel Desk must approve before HR Head.");
            //                 return;
            //             }

            //             // Prompt for remarks
            //             frappe.prompt([
            //                 {
            //                     fieldname: 'remarks_input',
            //                     label: `Enter ${button.label} Remarks`,
            //                     fieldtype: 'Data',
            //                     reqd: 1
            //                 }
            //             ],
            //                 function (values) {
            //                     // Set remarks
            //                     if (button.field === "hr_approval") {
            //                         frm.set_value('hr_remarks', values.remarks_input);
            //                     }
            //                     if (button.field === "travel_desk_approval") {
            //                         frm.set_value('travel_desk_remarks', values.remarks_input);
            //                     }
            //                     if (button.field === "hr_head_approval") {
            //                         frm.set_value('hr_head_remarks', values.remarks_input);
            //                         frm.set_value('status', 'Approved');
            //                     }
            //                     if (button.field === "reporting_head_approval") {
            //                         frm.set_value('reporting_head_remarks', values.remarks_input);
            //                     }

            //                     frm.set_value(button.field, 'Approved');
            //                     frm.refresh_field(button.field);

            //                     frm.save().then(() => {
            //                         // Trigger next-step email
            //                         if (button.field === "reporting_head_approval") {
            //                             send_email(frm.doc.name, "ReportingHead To HR");
            //                         }
            //                         if (button.field === "hr_approval") {
            //                             send_email(frm.doc.name, "HR To Travel Desk");

            //                         }
            //                         if (button.field === "travel_desk_approval") {
            //                             send_email(frm.doc.name, "Travel Desk To HRHead");

            //                         }
            //                         if (button.field === "hr_head_approval") {
            //                             send_email(frm.doc.name, "HRHead To PurchaseTeam");
            //                         }
            //                         updateStatus(frm); // refresh buttons
            //                     });
            //                 },
            //                 'Remarks Required',
            //                 'Submit');
            //         }
            //         by_button = true;
            //     });

            //     // Button styling
            //     btn.css({
            //         "background-color": status_color,
            //         "color": "white",
            //         "border-color": status_color,
            //         "cursor": (status === "Pending" && (designation === button.designation_match || designation === "Administrator")) ? "pointer" : "not-allowed"
            //     });

            //     // Disable button click if not allowed

            //     if (!(status === "Pending" && (designation === button.designation_match || designation === "Administrator"))) {

            //         btn.off("click");
            //     }
            // });
            
//     });
// }

function toggleFieldStatus(frm) {
    const fieldMap = {
        "Reporting Head": "reporting_head_approval",
        "HR": "hr_approval",
        "Travel Desk": "travel_desk_approval",
        "HR Head": "hr_head_approval"
    };

    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: {
            current_frappe_user: frappe.session.user
        },
        callback: function (r) {
            const designation = r.message;

            console.log("Car Indent Form Desingation +++++++++++++", designation, frappe.session.user, "+++++++++")

            if (designation && fieldMap[designation]) {
                frm.set_df_property(fieldMap[designation], "read_only", 0);
            }
            if (frappe.session.user === "Administrator") {
                Object.values(fieldMap).forEach(field => {

                    frm.set_df_property(field, "read_only", 0);
                });
            }

            if (designation === "Purchase" || designation === "Purchase Head" || designation === "Administrator") {
                frm.add_custom_button(__('Redirect to Purchase Form'), function () {
                    let currentUrl = window.location.href;
                    let urlParams = currentUrl.split('/');
                    let employeeName = decodeURIComponent(urlParams[urlParams.length - 1]);

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

        }
    });

    Object.keys(frm.fields_dict).forEach(function (fieldname) {
        frappe.call({
            method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
            args: {
                current_frappe_user: frappe.session.user
            },
            callback: function (r) {
                const userData = r.message;
                console.log("user data:", userData)

                if (userData === "Administrator") {
                    frm.set_df_property(fieldname, "read_only", 0);
                }
                else {
                    frm.set_df_property(fieldname, "read_only", 1);
                }
            }
        })
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
        frm.set_df_property('travel_desk_approval', 'read_only', 1);
        frm.set_df_property('travel_desk_remarks', 'read_only', 1);
        frm.set_df_property('default_currency', 'read_only', 1);
        frm.set_df_property('form_type', 'read_only', 1);
        frm.set_df_property('employee_code', 'read_only', 1);
        toggleFieldStatus(frm);
    },

    refresh: function (frm) {
        console.log("++++++user session=======================")
        updateStatus(frm);
        toggleFieldStatus(frm);
    },
    reporting_head_approval: function (frm) {
        if (by_button === true) {
            by_button = false;
            return;
        }
        if (frm.doc.reporting_head_approval && frm.doc.reporting_head_approval !== "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value("reporting_head_remarks", values.remarks_input);
                    frm.refresh_field("reporting_head_remarks");
                    frm.save().then(() => {
                        if (frm.doc.reporting_head_approval === "Approved") {
                            send_email(frm.doc.name, "ReportingHead To HR");
                        }
                        else if (frm.doc.reporting_head_approval === "Rejected") {
                            send_email(frm.doc.name, "Reject Reporting to Employee");
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
                    frm.set_value('reporting_head_remarks', values.remarks_input);
                    frm.refresh_field('reporting_head_remarks');
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

    hr_approval: function (frm) {
        if (by_button === true) {
            by_button = false;
            return;
        }
        if (frm.doc.reporting_head_approval !== "Approved") {
            frappe.msgprint("Reporting Head must approve before further approvals!");
            return;
        }
        if (frm.doc.hr_approval && frm.doc.hr_approval !== "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value("hr_remarks", values.remarks_input);
                    frm.refresh_field("hr_remarks");
                    frm.save().then(() => {
                        if (frm.doc.hr_approval === "Approved") {
                            send_email(frm.doc.name, "HR To Travel Desk");
                        }
                        else if (frm.doc.hr_approval === "Rejected") {
                            send_email(frm.doc.name, "Reject HRTeam to Employee");
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
                    frm.set_value('hr_remarks', values.remarks_input);
                    frm.refresh_field('hr_remarks');
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

    travel_desk_approval: function (frm) {
        if (by_button === true) {
            by_button = false;
            return;
        }
        if (frm.doc.hr_approval !== "Approved" && frm.doc.reporting_head_approval !== "Approved") {
            frappe.msgprint("Reporting Head and HR must approve before further approvals!");
            return;
        }
        if (frm.doc.travel_desk_approval && frm.doc.travel_desk_approval !== "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value("travel_desk_remarks", values.remarks_input);
                    frm.refresh_field("travel_desk_remarks");
                    frm.save().then(() => {
                        if (frm.doc.travel_desk_approval === "Approved") {
                            send_email(frm.doc.name, "Travel Desk To HRHead");
                        }
                        else if (frm.doc.travel_desk_approval === "Rejected") {
                            send_email(frm.doc.name, "Reject TravelDesk to Employee");
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
                    frm.set_value('travel_desk_remarks', values.remarks_input);
                    frm.refresh_field('travel_desk_remarks');
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

    hr_head_approval: function (frm) {
        if (by_button === true) {
            by_button = false;
            return;
        }

        console.log("insiderrr functionnnn")
        if (frm.doc.hr_approval !== "Approved" && frm.doc.reporting_head_approval !== "Approved" && frm.doc.travel_desk_approval !== "Approved") {
            frappe.msgprint("Reporting Head, HR and Travel Desk must approve before further approvals!");
            return;
        }

        // frm.doc.hr_head_approval &&
        if (frm.doc.hr_head_approval !== "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value("hr_head_remarks", values.remarks_input);
                    frm.refresh_field("hr_head_remarks");
                    frm.save().then(() => {
                        console.log("here we areeee")
                        if (frm.doc.hr_head_approval === "Approved") {
                            console.log("WE are approvinggg- hr head")
                            frm.set_value("status", "Approved");
                            send_email(frm.doc.name, "HRHead To PurchaseTeam");

                        }
                        else if (frm.doc.hr_head_approval === "Rejected") {
                            console.log("WE are rejecting- hr head")
                            frm.set_value("status", "Rejected");
                            send_email(frm.doc.name, "Reject HRHead to Employee");

                        }
                        frm.refresh_field("status");
                    });
                },
                'Remarks Required',
                'Submit'
            );
        } else {
            console.log("++++++++++++pending mei aa raha")
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value('hr_head_remarks', values.remarks_input);
                    frm.refresh_field('hr_head_remarks');
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
    }
});


