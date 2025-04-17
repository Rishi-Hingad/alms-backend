


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

function updateStatus(frm) {
    frm.clear_custom_buttons();

    const buttons = [
        {
            label: "Reporting Head",
            field: "reporting_head_approval",
            current_status: frm.doc.reporting_head_approval,
        },
        {
            label: "HR",
            field: "hr_approval",
            current_status: frm.doc.hr_approval,
        },
        {
            label: "HR Head",
            field: "hr_head_approval",
            current_status: frm.doc.hr_head_approval,
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

        frm.add_custom_button(`${button.label}: ${status}`, null).css({
            "background-color": status_color,
            "color": "white",
            "border-color": status_color,
            "cursor": "not-allowed"
        });
    });
}

function toggleFieldStatus(frm) {
    // alert('Hellow',frappe.session.designation)
    if (frappe.session.user === "reporting@gmail.com") {
        frm.set_df_property("reporting_head_approval", "read_only", 0);
    }
    if (frappe.session.user === "hr@gmail.com") {
        frm.set_df_property("hr_approval", "read_only", 0);
    } 
    if (frappe.session.user === "hrhead@gmail.com") {
        frm.set_df_property("hr_head_approval", "read_only", 0);
    } 

    if (frappe.session.user==="Administrator"){
        frm.set_df_property("reporting_head_approval", "read_only", 0);
        frm.set_df_property("hr_approval", "read_only", 0);
        frm.set_df_property("hr_head_approval", "read_only", 0);
    }


    if (frappe.session.user === "purchase@gmail.com") {
        frm.add_custom_button(__('Redirect to Purchase Form'), function() {
            let currentUrl = window.location.href;
                let urlParams = currentUrl.split('/'); // Split the URL by '/'
                let employeeName = decodeURIComponent(urlParams[urlParams.length - 1]);
                console.log("Employee Name ++++++++++++++++++++", employeeName)
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



    hr_approval: function(frm) {
        if (frm.doc.reporting_head_approval !== "Approved") {
            frappe.msgprint("Reporting Head must approve before HR can approve.");
            frm.set_value("hr_approval", "Pending");
            return;
        }
    
        if (frm.doc.hr_approval != "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ], 
            function(values) {
                frm.set_value('hr_remarks', values.remarks_input);
                frm.refresh_field('hr_remarks');
                frm.save().then(() => {
                    send_email(frm.doc.name, "HR To HRHead");
                });
            }, 
            'Remarks Required', 
            'Submit'
            );
        } else {
            frm.save_or_update();
        }
    },
    

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



    hr_head_approval: function(frm) {
        if (frm.doc.reporting_head_approval !== "Approved") {
            frappe.msgprint("Reporting Head must approve before HR Head can approve.");
            frm.set_value("hr_head_approval", "Pending");
            return;
        }
    
        if (frm.doc.hr_head_approval != "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ], 
            function(values) {
                frm.set_value('hr_head_remarks', values.remarks_input);
                frm.refresh_field('hr_head_remarks');
                frm.save().then(() => {
                    send_email(frm.doc.name, "HRHead To PurchaseTeam");
                    frm.set_value("status", "Approved");
                    frm.save_or_update();
                });
            }, 
            'Remarks Required', 
            'Submit'
            );
        } else {
            frm.save_or_update();
        }
    },
    
    refresh: function (frm) {
        updateStatus(frm);
        toggleFieldStatus(frm);
    }
});