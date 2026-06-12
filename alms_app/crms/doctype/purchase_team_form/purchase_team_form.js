let by_button = false;

/* ================================
 COMMON HELPERS
================================ */



function sendEmailSafe(name, type, payload = {}) {
    return frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name,
            email_send_to: type,
            payload
        }
    });
}



/* ================================
 VENDOR EMAIL MODULE
================================ */

function addVendorButton(frm, role) {
    if (!["finance team", "finance", "administrator"].includes(role)) return;

    const isApproved = frm.doc.status === "Approved";

    const alreadySent = frm.doc.email_sent_to_all === 1;

    const btn = frm.add_custom_button("Select Vendors", async () => {

        // Hard stop if disabled state somehow bypassed
        if (alreadySent) {
            frappe.msgprint("Emails already sent to all vendors.");
            return;
        }

        if (!isApproved) {
            frappe.msgprint("Approval required.");
            return;
        }

        const res = await frappe.db.get_list("Vendor Master", {
            fields: ["name", "contact_email"]
        });

        if (!res.length) {
            frappe.msgprint("No vendors found.");
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
                console.log("STEP 1: Button clicked");

                let selected = values.select_all
                    ? res.map(v => v.name)
                    : (values.vendors || []);
                console.log("STEP 2: Selected vendors", selected);

                if (!selected.length) {
                    frappe.msgprint("Select at least one vendor.");
                    return;
                }

                const btn = dialog.get_primary_btn();
                btn.prop("disabled", true).html("Sending...");

                try {
                    console.log("STEP 3: Before save");

                    if (frm.is_dirty() && frm.perm[0] && frm.perm[0].write) {
                        await frm.save();
                    }

                    console.log("STEP 4: After save");

                    console.log("STEP 5: Calling API");

                    console.log("PAYLOAD:", {
                        name: frm.doc.name,
                        email_send_to: selected
                    });

                    const response = await sendEmailSafe(
                        frm.doc.name,
                        "FinanceHead To Quotation Company",
                        {
                            email_send_to: selected,
                            send_to_all: values.select_all ? 1 : 0,
                            email_phase: "Initial",
                        }
                    );

                    console.log("STEP 6: API RESPONSE", response);

                    frappe.show_alert({
                        message: "Emails sent successfully",
                        indicator: "green"
                    });

                    dialog.hide();
                    await frm.reload_doc();

                } catch (e) {
                    console.error(e);

                    frappe.msgprint({
                        title: "Error",
                        indicator: "red",
                        message: "Something failed while sending emails."
                    });

                } finally {
                    btn.prop("disabled", false).text("Send Email");
                }
            }
        });

        dialog.show();

        // Toggle logic
        const selectAllField = dialog.fields_dict.select_all;
        const vendorField = dialog.fields_dict.vendors;

        selectAllField.$input.on("change", function () {
            const isChecked = dialog.get_value("select_all");

            if (isChecked) {
                $(vendorField.wrapper).closest('.frappe-control').hide();

                vendorField.df.options.forEach(opt => {
                    opt.checked = false;
                });

                vendorField.refresh();

            } else {
                $(vendorField.wrapper).closest('.frappe-control').show();
            }
        });
    });

    // Styling logic
    if (alreadySent) {
        btn.css({
            "background-color": "#6c757d",
            "color": "white",
            "cursor": "not-allowed",
            "opacity": "0.6"
        });

        btn.off("click");
    } else {
        btn.css({
            "background-color": isApproved ? "darkgreen" : "gray",
            "color": "white"
        });
    }

    // Badge (this is the visible audit signal)
    if (alreadySent) {
        frm.dashboard.add_indicator(
            "Emails already sent to all vendors",
            "green"
        );
    }
}

/* ================================
 MAIN UI ENTRY
================================ */
function applyAdminOverrides(frm, role) {
    const isAdmin = role === "administrator";

    frm.set_df_property("no_of_quotations", "read_only", isAdmin ? 0 : 1);
    frm.set_df_property("all_quotations_ref_no", "read_only", isAdmin ? 0 : 1);
}

async function updateUI(frm) {
    let role = "";
    if (frappe.user_roles.includes("Administrator")) role = "administrator";
    else if (frappe.user_roles.includes("Finance Team")) role = "finance team";
    else if (frappe.user_roles.includes("Finance")) role = "finance";
    frm.clear_custom_buttons();

    applyAdminOverrides(frm, role);
    addVendorButton(frm, role);
}

/* ================================
 FORM EVENTS
================================ */

frappe.ui.form.on("Purchase Team Form", {
    refresh(frm) {
        updateUI(frm);
        calculateTotals(frm);
        if (window.setup_approval_ui) {
            window.setup_approval_ui(frm);
        }

        let is_admin = frappe.user_roles.includes("Administrator");
        let legacy_status = {
            'purchase_team_status': 'purchase_team_remarks',
            'purchase_head_status': 'purchase_head_remarks',
            'status': 'status'
        };
        for (let [status_f, remark_f] of Object.entries(legacy_status)) {
            let val = frm.doc[status_f];
            let hidden = !is_admin && (val !== 'Approved' && val !== 'Rejected');
            frm.set_df_property(status_f, 'hidden', hidden);
            frm.set_df_property(remark_f, 'hidden', hidden);
        }
    },

    onload(frm) {
        frm.set_df_property("status", "read_only", true);

        let legacy_fields = [
            'purchase_team_status', 'purchase_team_remarks',
            'purchase_head_status', 'purchase_head_remarks', 'status'
        ];
        legacy_fields.forEach(f => frm.set_df_property(f, 'read_only', 1));
        
        let is_admin = frappe.user_roles.includes("Administrator");
        if (is_admin) {
            frm.set_df_property("is_submitted", "hidden", 0);
            frm.set_df_property("approval_initiated", "hidden", 0);
            frm.set_df_property("approval_entry", "hidden", 0);
        }
    },
    
    validate(frm) {
        if (!frm.doc.is_submitted) {
            frm.set_value("is_submitted", 1);
        }
    },
    kilometers_per_year: calculateTotals,
    tenure_in_years: calculateTotals,
    revised_ex_show_room_price: calculateTotals,
    revised_tcs: calculateTotals,
    revised_discount: calculateTotals,
    revised_accessories: calculateTotals,
    revised_registration_charges: calculateTotals
});

/* ================================
 CALCULATIONS
================================ */

function calculateTotals(frm) {
    const d = frm.doc;

    frm.set_value("total_kilometers", (d.kilometers_per_year || 0) * (d.tenure_in_years || 0));

    const net = (d.revised_ex_show_room_price || 0)
        + (d.revised_tcs || 0)
        - (d.revised_discount || 0);

    frm.set_value("revised_net_ex_showroom_price", net);

    frm.set_value("revised_financed_amount",
        net + (d.revised_accessories || 0) + (d.revised_registration_charges || 0)
    );
}