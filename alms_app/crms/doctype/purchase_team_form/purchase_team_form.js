
let by_button = false;

function updateStatus(frm) {
    // frm.clear_custom_buttons();

    frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: {
            current_frappe_user: frappe.session.user
        },
        callback: function (r) {
            const userDesignation = r.message;

            const stages = [
                {
                    label: "Purchase Team",
                    field: "purchase_team_status",
                    remarks_field: "purchase_team_remarks",
                    status: frm.doc.purchase_team_status,
                    role: "Purchase",
                    email_on_approve: "PurchaseTeam To PurchaseHead",
                    email_on_reject: "Reject PurchaseTeam to HR"
                },
                {
                    label: "Purchase Head",
                    field: "purchase_head_status",
                    remarks_field: "purchase_head_remarks",
                    status: frm.doc.purchase_head_status,
                    role: "Purchase Head",
                    email_on_approve: "PurchaseHead To FinanceTeam",
                    email_on_reject: "Reject PurchaseHead to PurchaseTeam"
                }
            ];

            const editableFields = {
                "Purchase": ["purchase_team_status"],
                "Purchase Head": ["purchase_head_status"],
                "Administrator": ["purchase_team_status", "purchase_head_status"]
            }[userDesignation] || [];

            const visibleFields = {
                "Purchase": ["purchase_team_status"],
                "Purchase Head": ["purchase_team_status", "purchase_head_status"],
                "Administrator": ["purchase_team_status", "purchase_head_status"]
            }[userDesignation] || [];

            stages.forEach(stage => {
                const status = stage.status || "Pending";
                const statusColor = {
                    "Approved": "darkgreen",
                    "Rejected": "darkred",
                    "Pending": "gray"
                }[status];

                if (visibleFields.includes(stage.field)) {
                    const canEdit = editableFields.includes(stage.field);

                    const btn = frm.add_custom_button(`${stage.label}: ${status}`, () => {
                        if (!canEdit) {
                            frappe.msgprint(`You can only view the status of ${stage.label}.`);
                            return;
                        }

                        if (stage.field === "purchase_head_status" && frm.doc.purchase_team_status !== "Approved") {
                            frappe.msgprint("Purchase Team must approve first.");
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

                                if (stage.field === "purchase_head_status") {
                                    frm.set_value("status", values.action_choice);
                                }

                                frm.save().then(() => {
                                    const action = values.action_choice;
                                    const email_type = action === "Approved" ? stage.email_on_approve : stage.email_on_reject;
                                    console.log(`[Email Trigger] ${stage.label} => ${action} => Email: ${email_type}`);
                                    if (email_type) {
                                        send_email(frm.doc.name, email_type);
                                    }
                                    updateStatus(frm);
                                });
                            },
                            'Action Required',
                            'Submit'
                        );

                        by_button = true;
                    });

                    btn.css({
                        "background-color": statusColor,
                        "color": "white",
                        "border-color": statusColor,
                        "cursor": canEdit ? "pointer" : "not-allowed",
                        "opacity": canEdit ? "1" : "0.6"
                    });

                    if (!canEdit) {
                        btn.off("click");
                    }
                }
            });

            if (["Administrator", "Finance", "Finance Head"].includes(userDesignation)) {
                frm.add_custom_button("Compare Quotations", () => {
                    frappe.call({
                        method: "frappe.client.get_list",
                        args: {
                            doctype: "Car Quotation",
                            filters: {
                                employee_details: frm.doc.name
                            },
                            fields: [
                                "name", "finance_company", "variant", "base_price_excluding_gst",
                                "gst", "total_emi", "interim_payment", "quarterly_payment", "status", "quotation_status",
                            ],
                            limit_page_length: 100
                        },
                        callback: function (res) {
                            const quotations = res.message;

                            if (!quotations || quotations.length === 0) {
                                frappe.msgprint("No Car Quotations found.");
                                return;
                            }

                            const fieldsToDisplay = [
                                { label: "Name", key: "name" },
                                { label: "Finance Company", key: "finance_company" },
                                { label: "Variant", key: "variant" },
                                { label: "Base Price (Excl. GST)", key: "base_price_excluding_gst" },
                                { label: "GST", key: "gst" },
                                { label: "Total EMI", key: "total_emi" },
                                { label: "Interim Payment", key: "interim_payment" },
                                { label: "Quarterly Payment", key: "quarterly_payment" },
                                { label: "Status", key: "status" },
                                { label: "Quotation Status", key: "quotation_status" },
                                { label: "Action", key: "action" },
                            ];

                            const tableHeader = quotations.map(q => `
                                <th style="text-align:center; background:#a3a1a1; font-weight:bold; font-size:18px;">
                                    ${q.finance_company || "-"}
                                </th>`).join("");

                            const tableRows = fieldsToDisplay.map(field => {
                                const rowCells = quotations.map(q => {
                                    if (field.key === "action") {
                                        return `
                                            <td style="text-align:center; background:#f9f9f9">
                                                <button class="btn btn-success btn-sm" 
                                                        onclick="approveQuotation('${q.name}', '${frm.doc.name}')" 
                                                        title="Approve Quotation">✔</button>
                            
                                                <button class="btn btn-danger btn-sm" 
                                                        onclick="rejectQuotation('${q.name}')" 
                                                        title="Reject Quotation">✖</button>
                                            </td>`;
                                    } else {
                                        return `<td style="text-align:center; background:#f9f9f9; font-size:16px; font-weight:medium;">
                                                    ${q[field.key] || "-"}
                                                </td>`;
                                    }
                                }).join("");

                                return `<tr>
                                    <th style="background:#a3a1a1; font-weight:bold; font-size:18px;">${field.label}</th>
                                    ${rowCells}
                                </tr>`;
                            }).join("");

                            const html = `
                                <div style="overflow-x:auto">
                                    <table class="table table-bordered table-sm" style="min-width:800px; background:#f7f7f7;">
                                        <thead><tr><th style="background:#a3a1a1; font-weight:bold; font-size:18px;">Fields</th>${tableHeader}</tr></thead>
                                        <tbody>${tableRows}</tbody>
                                    </table>
                                </div>
                            `;

                            const dialog = new frappe.ui.Dialog({
                                title: 'Compare Car Quotations',
                                fields: [
                                    {
                                        fieldtype: 'HTML',
                                        fieldname: 'quotation_table',
                                        options: html
                                    }
                                ],
                                size: 'extra-large'
                            });

                            dialog.show();

                            window.approveQuotation = function (approved_name, employee_details) {
                                frappe.prompt([
                                    {
                                        fieldname: 'remarks_input',
                                        label: 'Enter Finance Team Remarks',
                                        fieldtype: 'Data',
                                        reqd: 1
                                    }
                                ], function (values) {
                                    // 1. Update approved quotation status to Approved
                                    frappe.call({
                                        method: "frappe.client.set_value",
                                        args: {
                                            doctype: "Car Quotation",
                                            name: approved_name,
                                            fieldname: {
                                                status: "Approved",
                                                finance_team_status: "Approved",
                                                finance_team_remarks: values.remarks_input
                                            }
                                        },
                                        callback: function () {
                                            // 2. Reject all other quotations
                                            frappe.call({
                                                method: "frappe.client.get_list",
                                                args: {
                                                    doctype: "Car Quotation",
                                                    filters: {
                                                        employee_details: employee_details,
                                                        name: ["!=", approved_name]
                                                    },
                                                    fields: ["name"]
                                                },
                                                callback: function (res2) {
                                                    res2.message.forEach(other => {
                                                        frappe.call({
                                                            method: "frappe.client.set_value",
                                                            args: {
                                                                doctype: "Car Quotation",
                                                                name: other.name,
                                                                fieldname: { status: "Rejected" }
                                                            }
                                                        });
                                                    });

                                                    // 3. Send email using existing method
                                                    send_email(frm.doc.name, "FinanceTeam To FinanceHead Payload", { quotation_id: approved_name });

                                                    frappe.msgprint("Quotation approved, remarks saved, and email sent to Finance Head.");
                                                    dialog.hide();
                                                    updateStatus(frm);
                                                }
                                            });
                                        }
                                    });
                                }, 'Remarks Required', 'Submit');
                            };

                            window.rejectQuotation = function (name) {
                                frappe.prompt([
                                    {
                                        fieldname: 'remarks_input',
                                        label: 'Enter Finance Team Remarks for Rejection',
                                        fieldtype: 'Data',
                                        reqd: 1
                                    }
                                ], function (values) {
                                    frappe.call({
                                        method: "frappe.client.set_value",
                                        args: {
                                            doctype: "Car Quotation",
                                            name: name,
                                            fieldname: {
                                                status: "Rejected",
                                                finance_team_status: "Rejected",
                                                finance_team_remarks: values.remarks_input
                                            }
                                        },
                                        callback: function () {
                                            send_email(frm.doc.name, "Reject FinanceTeam to Vendor", { quotation_id: name }); // ✅ updated version
                                            frappe.msgprint("Quotation rejected, remarks saved, and notification sent.");
                                            dialog.hide();
                                            updateStatus(frm);
                                        }
                                    });
                                }, 'Remarks Required', 'Submit');
                            };

                        }
                    });
                });
            } else {
                frm.remove_custom_button("Compare Quotations");
            }

        }
    });
}
// old function to send quotation request to all companies do not delete by RISHI

// function updateQuotationSendRequest(frm) {
//     frm.add_custom_button('Quotations Company Select', () => {
//         // Fetch company names from Vendor Master where company names are stored in "name" field
//         frappe.db.get_list('Vendor Master', {
//             fields: ['name'], // Fetching name field as company name
//             distinct: true
//         }).then(response => {
//             let companies = [...new Set(response.map(item => item.name))]; // Unique values
//             let optionsHTML = '<div id="company-checkboxes">';

//             // Generating checkboxes dynamically
//             companies.forEach(company => {
//                 optionsHTML += `
//                     <label><input type="checkbox" name="company_select" value="${company}"> ${company}</label><br>
//                 `;
//             });

//             // Adding "ALL" option as default selected
//             optionsHTML += `<label><input type="checkbox" name="company_select" value="ALL"> ALL</label><br>`;
//             optionsHTML += '</div>';

//             // Show Prompt
//             frappe.prompt([
//                 {
//                     fieldname: 'company_select',
//                     label: 'Select Company',
//                     fieldtype: 'HTML',
//                     options: optionsHTML
//                 }
//             ], function () {
//                 // Get selected checkboxes
//                 let selected_companies = [];
//                 document.querySelectorAll('input[name="company_select"]:checked').forEach(checkbox => {
//                     selected_companies.push(checkbox.value);
//                 });

//                 // ✅ If "ALL" is selected, use all companies
//                 if (selected_companies.includes("ALL")) {
//                     selected_companies = companies;
//                 }
//                 console.log("Selected Companies: ", selected_companies);

//                 // ✅ Send email to all selected companies
//                 if (selected_companies.length > 0) {
//                     // alert(selected_companies)
//                     selected_companies.forEach(company => {
//                         console.log("Company Quotation", company)
//                         send_email(frm.doc.name, "FinanceHead To Quotation Company", {
//                             email_send_to: company
//                         });
//                         selected_companies = [];
//                     });
//                 } else {
//                     frappe.msgprint("Please select at least one company.");
//                 }

//                 document.querySelectorAll('#company-checkboxes input[type="checkbox"]').forEach(checkbox => {
//                     checkbox.checked = false;
//                 });

//                 // ✅ "ALL" checkbox remains checked by default
//                 //document.querySelector('input[value="ALL"]').checked = true;

//             }, 'Remarks Required', 'Submit');

//         });
//     }).css({
//         "background-color": "darkgreen",
//         "color": "white",
//         "border-color": "green",
//     });
// }

function updateQuotationSendRequest(frm) {
    const isApproved = frm.doc.purchase_team_status === "Approved" && frm.doc.purchase_head_status === "Approved";

    const btn = frm.add_custom_button('Quotations Company Select', () => {
        if (!isApproved) {
            frappe.msgprint("Quotations can only be sent after both Purchase Team and Purchase Head have approved.");
            return;
        }
        // Step 1: Fetch existing quotations for this Purchase Team
        frappe.db.get_list('Car Quotation', {
            filters: {
                employee_details: frm.doc.name
            },
            fields: ['finance_company'],
            limit: 100
        }).then(existingQuotations => {
            const sentCompanies = existingQuotations.map(q => q.finance_company);

            // Step 2: Fetch all vendor companies
            frappe.db.get_list('Vendor Master', {
                fields: ['name']
            }).then(response => {
                let companies = [...new Set(response.map(item => item.name))];

                let optionsHTML = '<div id="company-checkboxes">';
                optionsHTML += `<label><input type="checkbox" name="company_select" value="ALL"> ALL</label><br>`;
                companies.forEach(company => {
                    optionsHTML += `
                        <label><input type="checkbox" name="company_select" value="${company}"> ${company}</label><br>
                    `;
                });
                optionsHTML += '</div>';

                // Step 3: Show selection prompt
                frappe.prompt([
                    {
                        fieldname: 'company_select',
                        label: 'Select Company',
                        fieldtype: 'HTML',
                        options: optionsHTML
                    }
                ], function () {
                    let selected_companies = [];
                    document.querySelectorAll('input[name="company_select"]:checked').forEach(checkbox => {
                        selected_companies.push(checkbox.value);
                    });

                    if (selected_companies.includes("ALL")) {
                        selected_companies = companies;
                    }

                    if (selected_companies.length > 0) {
                        selected_companies.forEach(company => {
                            if (sentCompanies.includes(company)) {
                                setTimeout(() => {
                                    frappe.msgprint(`Quotation to <b>${company}</b> has already been sent.`);
                                }, delay);
                                delay += 600;
                            } else {
                                send_email(frm.doc.name, "FinanceHead To Quotation Company", {email_send_to: company});
                            }
                        });
                    } else {
                        frappe.msgprint("Please select at least one company.");
                    }
                    // Reset checkboxes
                    document.querySelectorAll('#company-checkboxes input[type="checkbox"]').forEach(checkbox => {
                        checkbox.checked = false;
                    });
                }, 'Remarks Required', 'Submit');
            });
        });
    });
    btn.css({
        "background-color": isApproved ? "darkgreen" : "gray",
        "color": "white",
        "border-color": isApproved ? "green" : "gray",
        "cursor": isApproved ? "pointer" : "not-allowed",
        "opacity": isApproved ? "1" : "0.6"
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
            else if (designation === "Purchase Head") {
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
            else if (designation === "Administrator") {
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
            } else {
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
        if (by_button === true) {
            frm.set_value("status", "Approved");

            by_button = false;
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
                    console.log("purchase status:", frm.doc.purchase_head_status)
                    frm.refresh_field('purchase_head_remarks');
                    frm.save().then(() => {
                        if (frm.doc.purchase_head_status === "Approved") {
                            frm.set_value("status", "Approved");
                        }
                        else if (frm.doc.purchase_head_status === "Rejected") {
                            frm.set_value("status", "Rejected");
                        }
                        // frm.set_value("status", "Approved");
                        frm.save_or_update();
                        if (frm.doc.purchase_head_status === "Approved") {
                            send_email(frm.doc.name, "PurchaseHead To FinanceTeam")
                        }
                        else if (frm.doc.purchase_head_status === "Rejected") {
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
        if (by_button === true) {
            by_button = false;

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
                        if (frm.doc.purchase_team_status === "Approved") {
                            send_email(frm.doc.name, "PurchaseTeam To PurchaseHead")
                        }
                        else if (frm.doc.purchase_team_status === "Rejected") {
                            send_email(frm.doc.name, "Reject PurchaseTeam to HR")
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


