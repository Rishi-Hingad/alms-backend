

function uploadfile(frm) {
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
    frm.add_custom_button('Send Modification Quot Email', function () {
        frappe.msgprint(__('Email sent successfully!')); 
        send_email(frm.doc.employee_details,"FinanceHead To Quotation Company",{"email_phase":"Modification","email_send_to":frm.doc.finance_company})
    }, 'Request Menu')
}


function setValuesInField(frm,data){
   
    const ListOfColumns  = [
        "finance_company","accessory","gst_and_cess",
        "employee_details","discount_excluding_gst","insurance",
        "location","base_price_less_discounts","fleet_management_repairs_and_tyres",
        "kms","total_discount","24x7_assist",
        "variant","ex_showroom_amount_net_of_discount","pickup_and_drop",
        "quote","registration_charges","pickup_and_drop",
        "interest_rate","residual_value_percent","std_relief_car_non_accdt",
        "tenure","financed_amount","gst_on_fms",
        "base_price_excluding_gst","financed_amount","total_emi",
        "gst","emi_financing","status",
        "ex_showroom_amount","finance_emi_road_tax"
    ]

    ListOfColumns.forEach(column =>{
        if (data[column] !== undefined) { 
            frm.set_value(column, data[column]);
        } else {
            frappe.msgprint(`${column} not found in data`);
        }
    })


}



function send_email(user,email_send_to,payload=null){
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name: user,
            email_send_to: email_send_to,
            payload: payload,
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
            label: "Finance Team",
            field: "finance_team_status",
            current_status: frm.doc.finance_team_status,
        },
        {
            label: "Finance Head",
            field: "finance_head_status",
            current_status: frm.doc.finance_head_status,
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

    Object.keys(frm.fields_dict).forEach(function(fieldname) {
        if (frappe.session.user === "financehead@gmail.com" && fieldname === "finance_head_status") {
             frm.set_df_property(fieldname, "read_only", 0);
        } else if (frappe.session.user === "finance@gmail.com" && fieldname === "finance_team_status") {
            frm.set_df_property(fieldname, "read_only", 0);
        } else {
            frm.set_df_property(fieldname, "read_only", 1);
        }
    });
}

frappe.ui.form.on('Car Quotation', {
    refresh: function (frm) {
        frm.set_df_property("status", "read_only", true);
        frm.set_df_property('status', 'read_only', 1);
        updateStatus(frm);
        toggleFieldStatus(frm);
        uploadfile(frm);


    },
    onload: function(frm) {
        frm.set_df_property("status", "read_only", true);
        updateStatus(frm);
        toggleFieldStatus(frm);
        uploadfile(frm);

    },
    
    finance_head_status:function(frm) {
        if (frm.doc.finance_head_status != "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ], 
            function(values) {
                frm.set_value('finance_head_remarks', values.remarks_input);
                frm.refresh_field('finance_head_remarks');
                frm.save().then(() => {
                    frm.set_value("status", "Approved");
                    send_email(frm.doc.employee_details,"FinanceHead To AccountsTeam")
                });
            }, 
            'Remarks Required', 
            'Submit'
            );
            
        }
        else{
            frm.save_or_update();
        }
    },



    finance_team_status: function(frm) {
        if (frm.doc.finance_team_status != "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ], 
            function(values) {
                frm.set_value('finance_team_remarks', values.remarks_input);
                frm.refresh_field('finance_team_remarks');
                frm.save().then(() => {
                    send_email(frm.doc.employee_details,"FinanceTeam To FinanceHead")
                });
            }, 
            'Remarks Required', 
            'Submit'
            );
        }
        else{
            frm.save_or_update();
        }
    },

});
