


function send_email(user,email_send_to){
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: { 
            name: user,
            email_send_to: email_send_to, 
        },
        callback: function (response) {
            if (!response.exc) {
                // frappe.msgprint("Email sent successfully!"); 
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

// function updateStatus(frm) {
//     frm.clear_custom_buttons();

//     const buttons = [
//         {
//             label: "Reporting Head",
//             field: "reporting_head_approval",
//             current_status: frm.doc.reporting_head_approval,
//         },
//         {
//             label: "HR",
//             field: "hr_approval",
//             current_status: frm.doc.hr_approval,
//         },
//         {
//             label: "HR Head",
//             field: "hr_head_approval",
//             current_status: frm.doc.hr_head_approval,
//         }
//     ];

//     buttons.forEach(button => {
//         const status = button.current_status || "Pending";
//         let status_color;

//         switch (status) {
//             case "Approved":
//                 status_color = "darkgreen";
//                 break;
//             case "Rejected":
//                 status_color = "darkred";
//                 break;
//             default:
//                 status_color = "gray";
//         }

//         frm.add_custom_button(`${button.label}: ${status}`, null).css({
//             "background-color": status_color,
//             "color": "white",
//             "border-color": status_color,
//             "cursor": "not-allowed"
//         });
//     });
// }



function updateStatus(frm) {
    frm.clear_custom_buttons();

    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: {
            current_frappe_user: frappe.session.user
        },
        callback: function (r) {
            const designation = r.message;

            const buttons = [
                {
                    label: "Reporting Head",
                    field: "reporting_head_approval",
                    current_status: frm.doc.reporting_head_approval,
                    designation_match: "Reporting Head"
                },
                {
                    label: "HR",
                    field: "hr_approval",
                    current_status: frm.doc.hr_approval,
                    designation_match: "HR"
                },
                {
                    label: "HR Head",
                    field: "hr_head_approval",
                    current_status: frm.doc.hr_head_approval,
                    designation_match: "HR Head"
                }
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

                // Default add button
                const btn = frm.add_custom_button(`${button.label}: ${status}`, () => {
                    // Only if status is pending AND designation matches
                    if (status === "Pending" && designation === button.designation_match) {
                        
                        // Additional check: reporting head must approve before HR/HR Head
                        if (button.field !== 'reporting_head_approval' && frm.doc.reporting_head_approval !== "Approved") {
                            frappe.msgprint("Reporting Head must approve before further approvals.");
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
                            if (button.field === "hr_approval") {
                                frm.set_value('hr_remarks', values.remarks_input);
                            }
                            if (button.field === "hr_head_approval") {
                                frm.set_value('hr_head_remarks', values.remarks_input);
                                frm.set_value('status', 'Approved');
                            }
                            frm.set_value(button.field, 'Approved');
                            frm.refresh_field(button.field);
                            frm.save().then(() => {
                                // Send email based on approval
                                if (button.field === "hr_approval") {
                                    send_email(frm.doc.name, "HR To HRHead");
                                }
                                if (button.field === "hr_head_approval") {
                                    send_email(frm.doc.name, "HRHead To PurchaseTeam");
                                }
                                updateStatus(frm); // Refresh buttons
                            });
                        },
                        'Remarks Required',
                        'Submit');
                    }
                });

                // Button styling
                btn.css({
                    "background-color": status_color,
                    "color": "white",
                    "border-color": status_color,
                    "cursor": (status === "Pending" && designation === button.designation_match) ? "pointer" : "not-allowed"
                });

                // Disable button click if not allowed
                if (!(status === "Pending" && designation === button.designation_match)) {
                    btn.off("click");
                }
            });
        }
    });
}


// function toggleFieldStatus(frm) {
//     // alert('Hellow',frappe.session.designation)

    
//     if (frappe.session.user === "reporting@gmail.com") {
//         frm.set_df_property("reporting_head_approval", "read_only", 0);
//     }
//     if (frappe.session.user === "hr@gmail.com") {
//         frm.set_df_property("hr_approval", "read_only", 0);
//     } 
//     if (frappe.session.user === "hrhead@gmail.com") {
//         frm.set_df_property("hr_head_approval", "read_only", 0);
//     } 

//     if (frappe.session.user==="Administrator"){
//         frm.set_df_property("reporting_head_approval", "read_only", 0);
//         frm.set_df_property("hr_approval", "read_only", 0);
//         frm.set_df_property("hr_head_approval", "read_only", 0);
//     }


//     if (frappe.session.user === "purchase@gmail.com") {
//         frm.add_custom_button(__('Redirect to Purchase Form'), function() {
//             let currentUrl = window.location.href;
//                 let urlParams = currentUrl.split('/'); // Split the URL by '/'
//                 let employeeName = decodeURIComponent(urlParams[urlParams.length - 1]);
//                 console.log("Employee Name ++++++++++++++++++++", employeeName)
//                 let apiUrl = `${window.location.origin}/app/purchase-team-form/new-purchase-team-form-?employee_name=${encodeURIComponent(employeeName)}`;
//             window.location.href = apiUrl;
//         }).css({
//             'background-color': '#007bff',
//             'color': 'white',
//             'border': 'none',
//             'padding': '10px 20px',
//             'font-size': '14px',  
//             'border-radius': '5px', 
//             'cursor': 'pointer'
//         });
//     }
// }









function toggleFieldStatus(frm) {
    const fieldMap = {
        "Reporting Manager": "reporting_head_approval",
        "HR": "hr_approval",
        "HR Head": "hr_head_approval"
    };

    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: {
            current_frappe_user: frappe.session.user
        },
        callback: function (r) {
            const designation = r.message;

            console.log("+++++++++++++",designation,frappe.session.user,"+++++++++")

            // Unlock specific approval field based on designation
            if (designation && fieldMap[designation]) {
                frm.set_df_property(fieldMap[designation], "read_only", 0);
            }
           
            // Admin has access to all approval fields
            if (frappe.session.user === "Administrator") {
                // console.log("Yess +++++++++++++++++++++++++++++++")
                Object.values(fieldMap).forEach(field => {

                    frm.set_df_property(field, "read_only", 1);
                });
            }

            // Purchase-specific behavior (custom button)
            if (designation === "Purchase" || designation === "Purchase Head") {
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

        toggleFieldStatus(frm);
    },

    // hr_approval:function(frm) {
    //     if (frm.doc.hr_approval != "Pending") {
    //         frappe.prompt([
    //             {
    //                 fieldname: 'remarks_input',
    //                 label: 'Enter Remarks',
    //                 fieldtype: 'Data',
    //                 reqd: 1
    //             }
    //         ], 
    //         function(values) {
    //             frm.set_value('hr_remarks', values.remarks_input);
    //             frm.refresh_field('hr_remarks');
    //             frm.save().then(() => {
    //                 send_email(frm.doc.name,"HR To HRHead")
    //             });
    //         }, 
    //         'Remarks Required', 
    //         'Submit'
    //         );
           
    //     }else{
    //         frm.save_or_update();
    //     }
    // },



    // hr_approval: function(frm) {
    //     if (frm.doc.reporting_head_approval !== "Approved") {
    //         frappe.msgprint("Reporting Head must approve before HR can approve.");
    //         frm.set_value("hr_approval", "Pending");
    //         return;
    //     }
    
    //     if (frm.doc.hr_approval != "Pending") {
    //         frappe.prompt([
    //             {
    //                 fieldname: 'remarks_input',
    //                 label: 'Enter Remarks',
    //                 fieldtype: 'Data',
    //                 reqd: 1
    //             }
    //         ], 
    //         function(values) {
    //             frm.set_value('hr_remarks', values.remarks_input);
    //             frm.refresh_field('hr_remarks');
    //             frm.save().then(() => {
    //                 send_email(frm.doc.name, "HR To HRHead");
    //             });
    //         }, 
    //         'Remarks Required', 
    //         'Submit'
    //         );
    //     } else {
    //         frm.save_or_update();
    //     }
    // },
    

    // hr_head_approval:function(frm) {
    //     if (frm.doc.hr_head_approval != "Pending") {
    //         frappe.prompt([
    //             {
    //                 fieldname: 'remarks_input',
    //                 label: 'Enter Remarks',
    //                 fieldtype: 'Data',
    //                 reqd: 1
    //             }
    //         ], 
    //         function(values) {
    //             console.log(11111)
    //             frm.set_value('hr_head_remarks', values.remarks_input);
    //             frm.refresh_field('hr_head_remarks');
    //             frm.save().then(() => {
    //                 console.log(1222222) 
    //                 send_email(frm.doc.name, "HRHead To PurchaseTeam");
    //                 frm.set_value("status", "Approved");
    //                 frm.save_or_update();
    //             });
    //         }, 
    //         'Remarks Required', 
    //         'Submit'
    //         );
            
    //     }
    //     else{
    //         frm.save_or_update();
    //     }
    // },



    // hr_head_approval: function(frm) {
    //     if (frm.doc.reporting_head_approval !== "Approved") {
    //         frappe.msgprint("Reporting Head must approve before HR Head can approve.");
    //         frm.set_value("hr_head_approval", "Pending");
    //         return;
    //     }
    
    //     if (frm.doc.hr_head_approval != "Pending") {
    //         frappe.prompt([
    //             {
    //                 fieldname: 'remarks_input',
    //                 label: 'Enter Remarks',
    //                 fieldtype: 'Data',
    //                 reqd: 1
    //             }
    //         ], 
    //         function(values) {
    //             frm.set_value('hr_head_remarks', values.remarks_input);
    //             frm.refresh_field('hr_head_remarks');
    //             frm.save().then(() => {
    //                 send_email(frm.doc.name, "HRHead To PurchaseTeam");
    //                 frm.set_value("status", "Approved");
    //                 frm.save_or_update();
    //             });
    //         }, 
    //         'Remarks Required', 
    //         'Submit'
    //         );
    //     } else {
    //         frm.save_or_update();
    //     }
    // },
    
    refresh: function (frm) {
        
        
        // const conf = get_conf()
        
        // // print(conf.redis_cache)
        console.log("++++++user session=======================")
        // config = frappe.get_site_config()
        // console.log(config.get("redis_cache"))

        
        updateStatus(frm);
        toggleFieldStatus(frm);




        
    }
    
});