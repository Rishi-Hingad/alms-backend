// Copyright (c) 2026, Rishi Hingad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Form", {
    refresh: function(frm) {
        if (typeof window.setup_approval_ui === "function") {
            window.setup_approval_ui(frm);
        }
        
        if (!frappe.user_roles.includes("System Manager") && frappe.session.user !== "Administrator") {
            if (frappe.user_roles.includes("Purchase Team") || frappe.user_roles.includes("Purchase Head")) {
                frm.set_df_property("quotation_document", "read_only", 1);
            }
        }
        
        if (frappe.session.user === "Administrator") {
            frm.add_custom_button(__('Force Delete'), () => {
                frappe.confirm(__('Are you sure you want to delete this Purchase Form, its Approval Entry, and the linked Selected Vendor entry?'), () => {
                    frappe.call({
                        method: "lease_app.crms.doctype.purchase_form.purchase_form.force_delete",
                        args: {
                            docname: frm.doc.name
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.set_route('List', 'Purchase Form');
                            }
                        }
                    });
                });
            }).removeClass('btn-default').addClass('btn-danger').css({
                'color': 'white',
                'background-color': '#dc3545',
                'border-color': '#dc3545'
            });
        }
        
        // Restore custom Select Vendors button
        addVendorButton(frm);
    },
    revised_ex_show_room_price: function(frm) { calculate_revised_fields(frm); },
    revised_discount: function(frm) { calculate_revised_fields(frm); },
    revised_tcs: function(frm) { calculate_revised_fields(frm); },
    revised_registration_charges: function(frm) { calculate_revised_fields(frm); },
    revised_accessories: function(frm) { calculate_revised_fields(frm); },
    kilometers_per_year: function(frm) { calculate_total_kilometers(frm); },
    tenure_in_years: function(frm) { calculate_total_kilometers(frm); },
    quotation_document: function(frm) { 
        if (!frm.is_new() && frm.is_dirty()) {
            setTimeout(() => {
                if (frm.is_dirty()) frm.save();
            }, 1000);
        }
    },
    revised_quotation_attachment_need_to_be_done: function(frm) {
        if (!frm.is_new() && frm.is_dirty()) {
            setTimeout(() => {
                if (frm.is_dirty()) frm.save();
            }, 1000);
        }
    }
});

function calculate_revised_fields(frm) {
    let ex_show_room = flt(frm.doc.revised_ex_show_room_price);
    let discount = flt(frm.doc.revised_discount);
    let tcs = flt(frm.doc.revised_tcs);
    let reg_charges = flt(frm.doc.revised_registration_charges);
    let accessories = flt(frm.doc.revised_accessories);

    let net_ex_show_room = ex_show_room - discount + tcs;
    let financed_amount = net_ex_show_room + reg_charges + accessories;

    frm.set_value("revised_net_ex_showroom_price", net_ex_show_room);
    frm.set_value("revised_financed_amount", financed_amount);
}

function calculate_total_kilometers(frm) {
    let km_per_year = flt(frm.doc.kilometers_per_year);
    let tenure = flt(frm.doc.tenure_in_years);
    
    if (km_per_year && tenure) {
        frm.set_value("total_kilometers", km_per_year * tenure);
    } else {
        frm.set_value("total_kilometers", "");
    }
}

function addVendorButton(frm) {
    if (!["Finance", "Administrator", "Finance Team", "Finance Head", "System Manager"].some(r => frappe.user_roles.includes(r))) return;

    const isApproved = frm.doc.purchase_team_status === "Approved" && frm.doc.purchase_head_status === "Approved";
    
    // Check if the generic approval status is Approved (to be compatible with new approval system)
    const isApprovedV2 = frm.doc.status === "Approved";

    const finalApproved = isApproved || isApprovedV2;

    const btn = frm.add_custom_button("Select Vendors", async () => {
        if (!finalApproved) {
            frappe.msgprint("Approval required from Purchase Team and Purchase Head first.");
            return;
        }

        const res = await frappe.db.get_list("Vendor Master", {
            fields: ["name", "contact_email"]
        });

        if (!res.length) {
            frappe.msgprint("No vendors found in Vendor Master.");
            return;
        }

        const dialog = new frappe.ui.Dialog({
            title: "Select Vendors",
            fields: [
                {
                    fieldname: "select_all",
                    fieldtype: "Check",
                    label: "Select All"
                },
                {
                    fieldname: "vendors",
                    fieldtype: "MultiCheck",
                    label: "Vendors",
                    options: res.map(v => ({
                        label: `${v.name} (${v.contact_email || "No Email"})`,
                        value: v.name
                    }))
                }
            ],
            primary_action_label: "Send Email",
            primary_action: async (values) => {
                let selected = [];

                if (values.select_all) {
                    selected = res.map(v => v.name);
                } else {
                    selected = values.vendors || [];
                }

                if (!selected.length) {
                    frappe.msgprint("Select at least one vendor.");
                    return;
                }

                const dBtn = dialog.get_primary_btn();
                dBtn.prop("disabled", true).html("Sending...");

                try {
                    await frappe.call({
                        method: "lease_app.api.emailsService.email_sender",
                        args: {
                            name: frm.doc.name,
                            email_send_to: "FinanceHead To Quotation Company",
                            payload: {
                                email_send_to: selected,
                                send_to_all: values.select_all ? 1 : 0
                            }
                        }
                    });
                    
                    frappe.msgprint("Emails sent successfully.");
                    dialog.hide();
                    frm.reload_doc();

                } catch (e) {
                    frappe.msgprint("Failed to send emails.");
                    dBtn.prop("disabled", false).text("Send Email");
                }
            }
        });

        dialog.show();

        /* ================================
           TOGGLE LOGIC (THE MAGIC)
        ================================ */
        const selectAllField = dialog.fields_dict.select_all;
        const vendorField = dialog.fields_dict.vendors;

        // listen for change
        selectAllField.$input.on("change", function () {
            const isChecked = dialog.get_value("select_all");

            if (isChecked) {
                // Hide vendor list
                $(vendorField.wrapper).closest('.frappe-control').hide();
                // Clear selection (important)
                dialog.set_value("vendors", []);
            } else {
                // Show vendor list again
                $(vendorField.wrapper).closest('.frappe-control').show();
            }
        });
    });

    btn.css({
        "background-color": finalApproved ? "darkgreen" : "gray",
        "color": "white"
    });
}
