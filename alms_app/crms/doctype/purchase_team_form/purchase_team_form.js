
let by_button=false
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

            const allowedDesignations = ["Purchase", "Purchase Head", "Administrator"];

            if (allowedDesignations.includes(userData)) {
                // frm.clear_custom_buttons();

                const buttons = [
                    {
                        label: "Purchase Team",
                        field: "status",
                        current_status: frm.doc.purchase_team_status,
                        //added here
                        designation_match:"Purchase",
                        btn_field:"purchase_team_status"
                    },
                    {
                        label: "Purchase Head",
                        field: "status",
                        current_status: frm.doc.purchase_head_status,
                        //added here
                        designation_match:"Purchase Head",
                        btn_field:"purchase_head_status"
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
                        if (status === "Pending" && (userData === button.designation_match || userData==="Administrator")) {
                            console.log("here")
                            if (button.btn_field !== 'purchase_team_status' && frm.doc.purchase_team_status !== "Approved") {
                                frappe.msgprint("Purchase Team must approve before further approvals.");
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
                                if (button.btn_field === "purchase_team_status") {
                                    frm.set_value('purchase_team_remarks', values.remarks_input);
                                }
                                if (button.btn_field === "purchase_head_status") {
                                    frm.set_value('purchase_head_remarks', values.remarks_input);
                                }

                                frm.set_value(button.btn_field, 'Approved');
                                frm.refresh_field(button.btn_field);

                                frm.save().then(() => {
                                    if (button.btn_field === "purchase_team_status") {
                                        send_email(frm.doc.name, "PurchaseTeam To PurchaseHead")
                                    }
                                    if (button.btn_field=== "purchase_head_status") {
                                        send_email(frm.doc.name, "PurchaseHead To FinanceTeam")
                                    }
                                    updateStatus(frm);
                                });
                            },
                            'Remarks Required',
                            'Submit');
                        }
                        by_button=true;

                    });
                    btn.css({
                        "background-color": status_color,
                        "color": "white",
                        "border-color": status_color,
                        "cursor": (status === "Pending" && (userData === button.designation_match || userData === "Administrator")) ? "pointer" : "not-allowed"
                    });
                    if (!(status === "Pending" && (userData === button.designation_match || userData=== "Administrator"))) {
                        btn.off("click");
                    }
                });
            }
        }
    });
}

function updateQuotationSendRequest(frm) {
    frm.add_custom_button('Quotations Company Select', () => {
        // Fetch company names from Vendor Master where company names are stored in "name" field
        frappe.db.get_list('Vendor Master', {
            fields: ['name'], // Fetching name field as company name
            distinct: true
        }).then(response => {
            let companies = [...new Set(response.map(item => item.name))]; // Unique values
            let optionsHTML = '<div id="company-checkboxes">';

            // Generating checkboxes dynamically
            companies.forEach(company => {
                optionsHTML += `
                    <label><input type="checkbox" name="company_select" value="${company}"> ${company}</label><br>
                `;
            });

            // Adding "ALL" option as default selected
            optionsHTML += `<label><input type="checkbox" name="company_select" value="ALL"> ALL</label><br>`;
            optionsHTML += '</div>';

            // Show Prompt
            frappe.prompt([
                {
                    fieldname: 'company_select',
                    label: 'Select Company',
                    fieldtype: 'HTML',
                    options: optionsHTML
                }
            ], function () {
                // Get selected checkboxes
                let selected_companies = [];
                document.querySelectorAll('input[name="company_select"]:checked').forEach(checkbox => {
                    selected_companies.push(checkbox.value);
                });

                // ✅ If "ALL" is selected, use all companies
                if (selected_companies.includes("ALL")) {
                    selected_companies = companies;
                }
                console.log("Selected Companies: ", selected_companies);

                // ✅ Send email to all selected companies
                if (selected_companies.length > 0) {
                    // alert(selected_companies)
                    selected_companies.forEach(company => {
                        console.log("Company Quotation", company)
                        send_email(frm.doc.name, "FinanceHead To Quotation Company", {
                            email_send_to: company
                        });
                        selected_companies = [];
                    });
                } else {
                    frappe.msgprint("Please select at least one company.");
                }

                document.querySelectorAll('#company-checkboxes input[type="checkbox"]').forEach(checkbox => {
                    checkbox.checked = false;
                });

                // ✅ "ALL" checkbox remains checked by default
                //document.querySelector('input[value="ALL"]').checked = true;

            }, 'Remarks Required', 'Submit');

        });
    }).css({
        "background-color": "darkgreen",
        "color": "white",
        "border-color": "green",
    });
}

function send_email(user, email_send_to, payload) {
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name: user,
            email_send_to: email_send_to,
            payload: payload
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


function toggleFieldStatus(frm) {

    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: {
            current_frappe_user: frappe.session.user
        },
        callback: function (r) {
            const designation = r.message;

            if (designation === "Purchase") {
                frm.set_df_property("purchase_head_status", "read_only", true);
                frm.set_df_property("purchase_head_remarks", "read_only", true);
                frm.set_df_property("purchase_team_remarks", "read_only", true);
            }
            else if(designation === "Purchase Head"){
                frm.set_df_property("status", "read_only", true);
                frm.set_df_property("purchase_team_status", "read_only", true);
                frm.set_df_property("kilometers_per_year", "read_only", true);
                frm.set_df_property("tenure_in_years", "read_only", true);
                frm.set_df_property("total_kilometers", "read_only", true);
                frm.set_df_property("revised_ex_show_room_price", "read_only", true);
                frm.set_df_property("revised_discount", "read_only", true);
                frm.set_df_property("revised_tcs", "read_only", true);
                frm.set_df_property("revised_net_ex_showroom_price", "read_only", true);
                frm.set_df_property("revised_registration_charges", "read_only", true);
                frm.set_df_property("revised_accessories", "read_only", true);
                frm.set_df_property("revised_financed_amount", "read_only", true);
                frm.set_df_property("status", "read_only", true);
                frm.set_df_property("purchase_head_remarks", "read_only", true);
                frm.set_df_property("purchase_team_remarks", "read_only", true);
            }
            else if(designation==="Administrator"){
                frm.set_df_property("status", "read_only", true);
                // frm.set_df_property("purchase_team_status", "read_only", true);
                frm.set_df_property("kilometers_per_year", "read_only", true);
                frm.set_df_property("tenure_in_years", "read_only", true);
                frm.set_df_property("total_kilometers", "read_only", true);
                frm.set_df_property("revised_ex_show_room_price", "read_only", true);
                frm.set_df_property("revised_discount", "read_only", true);
                frm.set_df_property("revised_tcs", "read_only", true);
                frm.set_df_property("revised_net_ex_showroom_price", "read_only", true);
                frm.set_df_property("revised_registration_charges", "read_only", true);
                frm.set_df_property("revised_accessories", "read_only", true);
                frm.set_df_property("revised_financed_amount", "read_only", true);
                frm.set_df_property("status", "read_only", true);
                frm.set_df_property("purchase_head_remarks", "read_only", true);
                frm.set_df_property("purchase_team_remarks", "read_only", true);
            }else{
                frm.set_df_property("status", "read_only", true);
                frm.set_df_property("purchase_team_status", "read_only", true);
                frm.set_df_property("kilometers_per_year", "read_only", true);
                frm.set_df_property("tenure_in_years", "read_only", true);
                frm.set_df_property("total_kilometers", "read_only", true);
                frm.set_df_property("revised_ex_show_room_price", "read_only", true);
                frm.set_df_property("revised_discount", "read_only", true);
                frm.set_df_property("revised_tcs", "read_only", true);
                frm.set_df_property("revised_net_ex_showroom_price", "read_only", true);
                frm.set_df_property("revised_registration_charges", "read_only", true);
                frm.set_df_property("revised_accessories", "read_only", true);
                frm.set_df_property("revised_financed_amount", "read_only", true);
                frm.set_df_property("status", "read_only", true);
                frm.set_df_property("purchase_head_remarks", "read_only", true);
                frm.set_df_property("purchase_team_remarks", "read_only", true);
                frm.set_df_property("purchase_head_status", "read_only", true);
            }
        }
    });
}


frappe.ui.form.on("Purchase Team Form", {
    // refresh(frm) {

    //     updateStatus(frm);
    //     frm.set_df_property("status", "read_only", true);
    //     if (frappe.session.user === "finance@gmail.com") {
    //         updateQuotationSendRequest(frm);
    //     }
    //     calculate_totals(frm);
    //     // addButtonForAppovel(frm);
    //     toggleFieldStatus(frm);
    // },
    // onload(frm) {
    //     // updateStatus(frm);
    //     frm.set_df_property("status", "read_only", true);
    //     if (frappe.session.user === "finance@gmail.com") {
    //         updateQuotationSendRequest(frm);
    //     }
    //     toggleFieldStatus(frm);
    //     // addButtonForAppovel(frm);
    // },

    refresh(frm) {
        updateStatus(frm);
        frappe.call({
            method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
            args: {
                current_frappe_user: frappe.session.user
            },
            callback: function (r) {
                const designation = r.message;

                if (designation == "Finance" || designation == "Administrator") {
                    updateQuotationSendRequest(frm);
                }

            }
        })
        calculate_totals(frm);
        // addButtonForAppovel(frm);
        toggleFieldStatus(frm);
    },

    onload(frm) {
        // updateStatus(frm);
        frm.set_df_property("status", "read_only", true);
        frappe.call({
            method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
            args: {
                current_frappe_user: frappe.session.user
            },
            callback: function (r) {
                const designation = r.message;

                if (designation == "Finance" || designation == "Administrator") {
                    updateQuotationSendRequest(frm);
                }

            }
        })
        toggleFieldStatus(frm);
        // addButtonForAppovel(frm);
    },

    //old
    purchase_head_status: function (frm) {
        if(by_button===true){
            frm.set_value("status", "Approved");
           
            by_button=false;
            frm.save_or_update();
            return;
        }
        if (frm.doc.purchase_head_status != "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value('purchase_head_remarks', values.remarks_input);
                    console.log("purchase status:",frm.doc.purchase_head_status)
                    frm.refresh_field('purchase_head_remarks');
                    frm.save().then(() => {
                        if(frm.doc.purchase_head_status==="Approved"){
                            frm.set_value("status", "Approved");
                        }
                        else if(frm.doc.purchase_head_status==="Rejected"){
                            frm.set_value("status", "Rejected");
                        }
                        // frm.set_value("status", "Approved");
                        frm.save_or_update();
                        if(frm.doc.purchase_head_status==="Approved"){
                            send_email(frm.doc.name, "PurchaseHead To FinanceTeam")
                        }
                        else if(frm.doc.purchase_head_status==="Rejected"){
                            // send email to Purchase Team
                            send_email(frm.doc.name, "Reject PurchaseHead to PurchaseTeam")
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
                    frm.set_value('purchase_head_remarks', values.remarks_input);
                    frm.refresh_field('purchase_head_remarks');
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


    purchase_team_status: function (frm) {
        if(by_button===true){
            by_button=false;

            return;
        }
        if (frm.doc.purchase_team_status && frm.doc.purchase_team_status !== "Pending") {
            frappe.prompt([
                {
                    fieldname: 'remarks_input',
                    label: 'Enter Remarks',
                    fieldtype: 'Data',
                    reqd: 1
                }
            ],
                function (values) {
                    frm.set_value('purchase_team_remarks', values.remarks_input);
                    frm.refresh_field('purchase_team_remarks');
                    frm.save().then(() => {
                        if(frm.doc.purchase_team_status==="Approved"){
                            send_email(frm.doc.name, "PurchaseTeam To PurchaseHead")
                        }
                        else{  
                            console.log("rejected")
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
                    frm.set_value('purchase_team_remarks', values.remarks_input);
                    frm.refresh_field('purchase_team_remarks');
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

    // purchase_head_status: function(frm, cdt, cdn) {
    //     const doc = frappe.get_doc(cdt, cdn);
    //     // Skip if this is coming from a button click (handled by the button)
    //     if (doc.__from_button_click) {
    //         delete doc.__from_button_click;
    //         return;
    //     }
        
    //     // Only handle if the value actually changed
    //     if (doc.__unsaved || doc.purchase_head_status !== doc.__last_purchase_head_status) {
    //         handleStatusUpdate(
    //             frm, 
    //             "purchase_head_status", 
    //             "purchase_head_remarks", 
    //             "PurchaseHead To FinanceTeam",
    //             doc.purchase_head_status
    //         ).then(() => {
    //             updateStatus(frm);
    //             doc.__last_purchase_head_status = doc.purchase_head_status;
    //         });
    //     }
    // },

    // purchase_team_status: function(frm, cdt, cdn) {
    //     const doc = frappe.get_doc(cdt, cdn);
    //     // Skip if this is coming from a button click (handled by the button)
    //     if (doc.__from_button_click) {
    //         delete doc.__from_button_click;
    //         return;
    //     }
        
    //     // Only handle if the value actually changed
    //     if (doc.__unsaved && doc.purchase_team_status !== doc.__last_purchase_team_status) {
    //         handleStatusUpdate(
    //             frm, 
    //             "purchase_team_status", 
    //             "purchase_team_remarks", 
    //             "PurchaseTeam To PurchaseHead",
    //             doc.purchase_team_status
    //         ).then(() => {
    //             updateStatus(frm);
    //             doc.__last_purchase_team_status = doc.purchase_team_status;
    //         });
    //     }
    // },
    revised_ex_show_room_price: function (frm) {
        calculate_totals(frm);
    },

    revised_discount: function (frm) {
        calculate_totals(frm);
    },

    revised_tcs: function (frm) {
        calculate_totals(frm);
    },

    revised_registration_charges: function (frm) {
        calculate_totals(frm);
    },

    revised_accessories: function (frm) {
        calculate_totals(frm);
    },

    kilometers_per_year: function (frm) {
        calculate_totals(frm);
    },

    tenure_in_years: function (frm) {
        calculate_totals(frm);
    },


});


function calculate_totals(frm) {
    const revised_ex_show_room_price = frm.doc.revised_ex_show_room_price || 0;
    const revised_tcs = frm.doc.revised_tcs || 0;
    const revised_accessories = frm.doc.revised_accessories || 0;
    const revised_discount = frm.doc.revised_discount || 0;
    const revised_registration_charges = frm.doc.revised_registration_charges || 0;
    const kilometers_per_year = frm.doc.kilometers_per_year || 0;
    const tenure_in_years = frm.doc.tenure_in_years || 0;

    frm.set_value("total_kilometers", kilometers_per_year * tenure_in_years);

    const revised_net_ex_showroom_price = revised_ex_show_room_price + revised_tcs - revised_discount;
    frm.set_value("revised_net_ex_showroom_price", revised_net_ex_showroom_price);

    const finance_amount = (revised_ex_show_room_price + revised_tcs - revised_discount) + revised_accessories + revised_registration_charges;
    frm.set_value("revised_financed_amount", finance_amount);
}


