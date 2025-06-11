//latest
// function handleStatusUpdate(frm, status_field, remarks_field, email_template, new_status) {
//     return new Promise((resolve) => {
//         // Always show remarks prompt for any status change
//         frappe.prompt([
//             {
//                 fieldname: 'remarks_input',
//                 label: `Enter Remarks`,
//                 fieldtype: 'Data',
//                 reqd: 1
//             }
//         ], (values) => {
//             // Set remarks and status
//             frm.set_value(remarks_field, values.remarks_input);
//             frm.set_value(status_field, new_status);
//             // console.log(values.remarks_input)
//             // console.log("hello")
//             // console.log(status_field==='purchase_head_status')
//             // console.log(new_status==='Approved')
//             // if(status_field==='purchase_head_status' && new_status==='Approved'){
//             //     frm.set_value('status','Approved')
//             // }
            
//             frm.save().then(() => {
//                 // Send email only for Approved/Rejected
//                 if (["Approved", "Rejected"].includes(new_status)) {
//                     send_email(frm.doc.name, email_template);
//                 }
//                 resolve();
//             });
//         }, 'Remarks Required', 'Submit');
//     });
// }

// // Unified status update function
// function updateStatus(frm) {
//     frm.clear_custom_buttons();
    
//     frappe.call({
//         method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
//         args: { current_frappe_user: frappe.session.user },
//         callback: function(r) {
//             const userData = r.message;
//             if (!userData) return;

//             const allowedDesignations = ["Purchase", "Purchase Head"];
//             if (!allowedDesignations.includes(userData)) return;

//             const buttons = [
//                 {
//                     label: "Purchase Team",
//                     status_field: "purchase_team_status",
//                     remarks_field: "purchase_team_remarks",
//                     designation_match: "Purchase",
//                     email_template: "PurchaseTeam To PurchaseHead"
//                 },
//                 {
//                     label: "Purchase Head",
//                     status_field: "purchase_head_status",
//                     remarks_field: "purchase_head_remarks",
//                     designation_match: "Purchase Head",
//                     email_template: "PurchaseHead To FinanceTeam"
//                 }
//             ];

//             buttons.forEach(button => {
//                 const current_status = frm.doc[button.status_field] || "Pending";
//                 const status_color = {
//                     "Approved": "darkgreen",
//                     "Rejected": "darkred",
//                     "Pending": "gray"
//                 }[current_status];

//                 const btn = frm.add_custom_button(
//                     `${button.label}: ${current_status}`,
//                     async () => {
//                         if (current_status === "Pending" && userData === button.designation_match) {
//                             // Enforce sequential approval
//                             if (button.status_field === 'purchase_head_status' && 
//                                 frm.doc.purchase_team_status !== "Approved") {
//                                 frappe.msgprint("Purchase Team must approve first.");
//                                 return;
//                             }

//                             await handleStatusUpdate(
//                                 frm, 
//                                 button.status_field, 
//                                 button.remarks_field, 
//                                 button.email_template,
//                                 "Approved" // Button always approves
//                             );
                            
//                             updateStatus(frm); // Refresh buttons
//                         }
//                     }
//                 );

//                 // Button styling
//                 btn.css({
//                     "background-color": status_color,
//                     "color": "white",
//                     "border-color": status_color,
//                     "cursor": (current_status === "Pending" && userData === button.designation_match) 
//                         ? "pointer" : "not-allowed"
//                 });

//                 if (!(current_status === "Pending" && userData === button.designation_match)) {
//                     btn.off("click");
//                 }
//             });
//         }
//     });
// }


// latest
// function updateStatus(frm) {
//     frm.clear_custom_buttons();
    
//     frappe.call({
//         method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
//         args: { current_frappe_user: frappe.session.user },
//         callback: function(r) {
//             const userData = r.message;
//             if (!userData) return;

//             const allowedDesignations = ["Purchase", "Purchase Head"];
//             if (!allowedDesignations.includes(userData)) return;

//             const buttons = [
//                 {
//                     label: "Purchase Team",
//                     status_field: "purchase_team_status",
//                     remarks_field: "purchase_team_remarks",
//                     designation_match: "Purchase",
//                     email_template: "PurchaseTeam To PurchaseHead"
//                 },
//                 {
//                     label: "Purchase Head",
//                     status_field: "purchase_head_status",
//                     remarks_field: "purchase_head_remarks",
//                     designation_match: "Purchase Head",
//                     email_template: "PurchaseHead To FinanceTeam"
//                 }
//             ];

//             buttons.forEach(button => {
//                 const current_status = frm.doc[button.status_field] || "Pending";
//                 const status_color = {
//                     "Approved": "darkgreen",
//                     "Rejected": "darkred",
//                     "Pending": "gray"
//                 }[current_status];

//                 const btn = frm.add_custom_button(
//                     `${button.label}: ${current_status}`,
//                     () => {} // Empty handler, we'll attach the real one below
//                 );

//                 // Only make the button clickable if it's Pending and matches user's designation
//                 if (current_status === "Pending" && userData === button.designation_match) {
//                     btn.on("click", async () => {
//                         // Enforce sequential approval
//                         if (button.status_field === 'purchase_head_status' && 
//                             frm.doc.purchase_team_status !== "Approved") {
//                             frappe.msgprint("Purchase Team must approve first.");
//                             return;
//                         }

//                         // Mark that this is coming from a button click
//                         frm.doc.__from_button_click = true;
//                         console.log(frm.doc.__from_button_click)  ///
//                         await handleStatusUpdate(
//                             frm, 
//                             button.status_field, 
//                             button.remarks_field, 
//                             button.email_template,
//                             "Approved" // Button always approves
//                         );
                        
//                         updateStatus(frm); // Refresh buttons
//                     });
//                 }

//                 // Button styling
//                 btn.css({
//                     "background-color": status_color,
//                     "color": "white",
//                     "border-color": status_color,
//                     "cursor": (current_status === "Pending" && userData === button.designation_match) 
//                         ? "pointer" : "not-allowed"
//                 });

//                 // Disable hover effects for non-clickable buttons
//                 if (!(current_status === "Pending" && userData === button.designation_match)) {
//                     btn.off("click");
//                 }
//             });
//         }
//     });
// }

//decent working

let by_button=false
function updateStatus(frm) {
    frm.clear_custom_buttons();
    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: {
            current_frappe_user: frappe.session.user
        },
        callback: function (r) {
            const userData = r.message;

            console.log("User Data", userData, "+++++++++++++++++++++++++++++")

            if (!userData) return;

            const allowedDesignations = ["Purchase", "Purchase Head"];

            if (allowedDesignations.includes(userData)) {
                frm.clear_custom_buttons();

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
                            // Enforce sequential approval
                            if (button.btn_field !== 'purchase_team_status' && frm.doc.purchase_team_status !== "Approved") {
                                frappe.msgprint("Purchase Team must approve before further approvals.");
                                return;
                            }

                            // Prompt for remarks
                            frappe.prompt([
                                {
                                    fieldname: 'remarks_input',
                                    label: `Enter ${button.label} Remarks`,
                                    fieldtype: 'Data',
                                    reqd: 1
                                }
                            ],
                            function (values) {
                                // Set remarks
                                if (button.btn_field === "purchase_team_status") {
                                    frm.set_value('purchase_team_remarks', values.remarks_input);
                                }
                                if (button.btn_field === "purchase_head_status") {
                                    frm.set_value('purchase_head_remarks', values.remarks_input);
                                }

                                frm.set_value(button.btn_field, 'Approved');
                                frm.refresh_field(button.btn_field);

                                frm.save().then(() => {
                                    // Trigger next-step email
                                    //email check kara tha
                                    if (button.btn_field === "purchase_team_status") {
                                        send_email(frm.doc.name, "PurchaseTeam To PurchaseHead")
                                    }
                                    if (button.btn_field=== "purchase_head_status") {
                                        send_email(frm.doc.name, "PurchaseHead To FinanceTeam")
                                        
                                    }

                                    updateStatus(frm); // refresh buttons
                                });
                            },
                            'Remarks Required',
                            'Submit');
                        }
                        by_button=true;

                    });
                    // Button styling
                    btn.css({
                        "background-color": status_color,
                        "color": "white",
                        "border-color": status_color,
                        "cursor": (status === "Pending" && (userData === button.designation_match || userData === "Administrator")) ? "pointer" : "not-allowed"
                    });

                    // Disable button click if not allowed
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
                    selected_companies = companies;  // Select all companies dynamically
                }

                // ✅ Debugging (Remove alert if not needed)
                console.log("Selected Companies: ", selected_companies);

                // ✅ Send email to all selected companies
                if (selected_companies.length > 0) {
                    // alert(selected_companies)
                    selected_companies.forEach(company => {
                        console.log("Company Quotation", company)
                        send_email(frm.doc.name, "FinanceHead To Quotation Company", {
                            email_send_to: company
                            // selected_companies.p
                        });
                        selected_companies = [];
                    });
                } else {
                    frappe.msgprint("Please select at least one company.");
                }

                // ✅ Clear selected checkboxes after submission
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


// function toggleFieldStatus(frm) {


// if (frappe.session.user === "purchase@gmail.com") {
//     frm.set_df_property("purchase_head_status", "read_only", true);
//     frm.set_df_property("purchase_head_remarks", "read_only", true);
//     frm.set_df_property("purchase_team_remarks", "read_only", true);
// }
// else{
//         frm.set_df_property("status", "read_only", true);
//         frm.set_df_property("purchase_team_status", "read_only", true);
//         frm.set_df_property("kilometers_per_year", "read_only", true);
//         frm.set_df_property("tenure_in_years", "read_only", true);
//         frm.set_df_property("total_kilometers", "read_only", true);
//         frm.set_df_property("revised_ex_show_room_price", "read_only", true);
//         frm.set_df_property("revised_discount", "read_only", true);
//         frm.set_df_property("revised_tcs", "read_only", true);
//         frm.set_df_property("revised_net_ex_showroom_price", "read_only", true);
//         frm.set_df_property("revised_registration_charges", "read_only", true);
//         frm.set_df_property("revised_accessories", "read_only", true);
//         frm.set_df_property("revised_financed_amount", "read_only", true);
//         frm.set_df_property("status", "read_only", true);
//         frm.set_df_property("purchase_head_remarks", "read_only", true);
//         frm.set_df_property("purchase_team_remarks", "read_only", true);
// }






// }



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

                if (designation == "Finance") {
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

                if (designation == "Finance") {
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


