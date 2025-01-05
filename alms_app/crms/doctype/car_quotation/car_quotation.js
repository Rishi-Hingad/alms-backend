

function uploadfile(frm){
    frm.add_custom_button('Upload and Process File', function () {
        frappe.prompt(
            {
                label: 'Upload File',
                fieldname: 'file',
                fieldtype: 'Attach',
                reqd: 1,
            },
            function (values) {
                frappe.call({
                    method: 'alms_app.crms.doctype.car_quotation.car_quotation.process_uploaded_file',
                    args: {
                        file_url: values.file,
                    },
                    callback: function (response) {
                        if (response.message) {
                            setValuesInField(frm,response.message.car_quotation_item)
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
    });
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
        "ex_showroom_amount","finance_emi_road_tax","finance_hod_status"
    ]

    ListOfColumns.forEach(column =>{
        if (data[column] !== undefined) { 
            frm.set_value(column, data[column]);
        } else {
            frappe.msgprint(`${column} not found in data`);
        }
    })


}


function changeStatus(frm, field_to_update, new_status) {
    frm.set_value(field_to_update, new_status); // Update the specified field with the new status

    if (field_to_update === "finance_hod_status" && new_status === "Approved") {
        frm.set_value("status", true); // Set the status field to true
    }
    
    frm.save()
        .then(function () {
            frm.refresh_field(field_to_update); // Refresh the updated field
            frm.clear_custom_buttons(); // Clear buttons
            

        })
        .catch(function (error) {
            frappe.msgprint(__('Error saving document: ') + error.message); // Display error if save fails
        });
}

function setApproveButton(frm) {
    // frm.clear_custom_buttons(); // Remove existing buttons
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

                // Set read-only fields based on designation
                if (designation === "Finance") {
                    frm.set_df_property('finance_hod_status', 'read_only', 1);
                }
                if (designation === "Finance Head") {
                    frm.set_df_property('finance_team_status', 'read_only', 1);
                }

                // Define button configurations
                const buttons = [
                    {
                        label: frm.doc.finance_team_status === "Rejected"
                            ? "Rejected by Finance Team"
                            : frm.doc.finance_team_status === "Approved"
                                ? "Approved by Finance Team"
                                : "Approve or Reject by Finance Team",
                        field: "finance_team_status",
                        current_status: frm.doc.finance_team_status,
                        designation: "Finance",
                        enabled: designation === "Finance",
                        colors: {
                            approved: "green",
                            rejected: "darkred",
                            pending: "lightgreen",
                            disabled: "lightgray"
                        }
                    },
                    {
                        label: frm.doc.finance_hod_status === "Rejected"
                            ? "Rejected by Finance Head"
                            : frm.doc.finance_hod_status === "Approved"
                                ? "Approved by Finance Head"
                                : "Approve or Reject by Finance Head",
                        field: "finance_hod_status",
                        current_status: frm.doc.finance_hod_status,
                        designation: "Finance Head",
                        enabled: designation === "Finance Head",
                        colors: {
                            approved: "green",
                            rejected: "darkred",
                            pending: "lightgreen",
                            disabled: "lightgray"
                        }
                    }
                ];

                // Add buttons with appropriate styles and actions
                buttons.forEach(button => {
                    const btn_color =
                        button.current_status === "Approved"
                            ? button.colors.approved
                            : button.current_status === "Rejected"
                                ? button.colors.rejected
                                : button.enabled
                                    ? button.colors.pending
                                    : button.colors.disabled;

                    const btn = frm.add_custom_button(button.label, function () {
                        if (button.enabled && button.current_status === "Pending") {
                            frappe.prompt(
                                {
                                    label: __('Approve or Reject'),
                                    fieldname: 'action',
                                    fieldtype: 'Select',
                                    options: ['Approved', 'Rejected'],
                                    reqd: 1
                                },
                                function (data) {
                                    changeStatus(frm, button.field, data.action);
                                },
                                __('Select Action'),
                                __('Submit')
                            );
                        } else if (!button.enabled) {
                            frappe.msgprint(__('You are not allowed to perform this action.'));
                        }
                    });

                    // Apply button styles
                    btn.css({
                        "background-color": btn_color,
                        "color": "white",
                        "border-color": btn_color === "red" ? "darkred" : "darkgreen",
                        "cursor": button.enabled ? "pointer" : "not-allowed"
                    });
                });
            }
        }
    });
}


frappe.ui.form.on('Car Quotation', {
    refresh: function (frm) {
        frm.set_df_property('status', 'read_only', 1);
        uploadfile(frm);
        setApproveButton(frm);


    },
    onload: function(frm) {
        setApproveButton(frm);

    }
});
