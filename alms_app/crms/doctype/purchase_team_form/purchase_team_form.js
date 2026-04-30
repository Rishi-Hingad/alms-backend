let by_button = false;

/* ================================
 COMMON HELPERS
================================ */

function getUserDesignation() {
    return frappe.call({
        method: "alms_app.crms.doctype.car_indent_form.car_indent_form.management",
        args: { current_frappe_user: frappe.session.user }
    });
}

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

function promptAction(label) {
    return new Promise(resolve => {
        frappe.prompt([
            {
                fieldname: 'action',
                label: `Action for ${label}`,
                fieldtype: 'Select',
                options: ['Approved', 'Rejected'],
                reqd: 1
            },
            {
                fieldname: 'remarks',
                label: `Remarks`,
                fieldtype: 'Data',
                reqd: 1
            }
        ], resolve, 'Action Required', 'Submit');
    });
}

/* ================================
 STATUS BUTTON ENGINE
================================ */

function buildStatusButtons(frm, role) {
    // frm.clear_custom_buttons();

    const config = [
        {
            label: "Purchase Team",
            field: "purchase_team_status",
            remarks: "purchase_team_remarks",
            depends_on: null,
            email: {
                Approved: "PurchaseTeam To PurchaseHead",
                Rejected: "Reject PurchaseTeam to HR"
            }
        },
        {
            label: "Purchase Head",
            field: "purchase_head_status",
            remarks: "purchase_head_remarks",
            depends_on: "purchase_team_status",
            email: {
                Approved: "PurchaseHead To FinanceTeam",
                Rejected: "Reject PurchaseHead to PurchaseTeam"
            }
        }
    ];

    const permissions = {
        "purchase": ["purchase_team_status"],
        "purchase head": ["purchase_head_status"],
        "administrator": ["purchase_team_status", "purchase_head_status"]
    };

    config.forEach(stage => {
        const status = frm.doc[stage.field] || "Pending";
        const canEdit = permissions[role]?.includes(stage.field);

        const btn = frm.add_custom_button(
            `${stage.label}: ${status}`,
            async () => {
                if (!canEdit) {
                    frappe.msgprint("Read only access.");
                    return;
                }

                if (
                    role !== "administrator" &&
                    stage.depends_on &&
                    frm.doc[stage.depends_on] !== "Approved"
                ) {
                    frappe.msgprint("Previous stage must be approved first.");
                    return;
                }

                by_button = true;

                try {
                    const values = await promptAction(stage.label);

                    frm.set_value(stage.field, values.action);
                    frm.set_value(stage.remarks, values.remarks);

                    if (frm.is_dirty()) {
                        await frm.save();
                    }

                    await sendEmailSafe(
                        frm.doc.name,
                        stage.email[values.action]
                    );

                    updateUI(frm);

                } finally {
                    by_button = false;
                }
            }
        );

        styleButton(btn, status, canEdit);
    });
}

function styleButton(btn, status, canEdit) {
    const colors = {
        Approved: "darkgreen",
        Rejected: "darkred",
        Pending: "gray"
    };

    btn.css({
        "background-color": colors[status],
        "color": "white",
        "cursor": canEdit ? "pointer" : "not-allowed",
        "opacity": canEdit ? 1 : 0.6
    });

    if (!canEdit) btn.off("click");
}

/* ================================
 VENDOR EMAIL MODULE
================================ */

function addVendorButton(frm, role) {
    if (!["finance", "administrator"].includes(role)) return;

    const isApproved =
        frm.doc.purchase_team_status === "Approved" &&
        frm.doc.purchase_head_status === "Approved";

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

                    if (frm.is_dirty()) {
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

    if (isAdmin) {
        frm.set_df_property("purchase_team_status", "read_only", false);
        frm.set_df_property("purchase_head_status", "read_only", false);

        frm.set_df_property("purchase_team_remarks", "read_only", false);
        frm.set_df_property("purchase_head_remarks", "read_only", false);
    }

    frm.set_df_property("no_of_quotations", "read_only", isAdmin ? 0 : 1);
    frm.set_df_property("all_quotations_ref_no", "read_only", isAdmin ? 0 : 1);
}

async function updateUI(frm) {

    const r = await getUserDesignation();
    const role = (r.message || "").trim().toLowerCase();
    frm.clear_custom_buttons();


    applyAdminOverrides(frm, role);

    buildStatusButtons(frm, role);

    addVendorButton(frm, role);
}

/* ================================
 FORM EVENTS
================================ */

frappe.ui.form.on("Purchase Team Form", {
    refresh(frm) {
        updateUI(frm);
        calculateTotals(frm);
    },

    onload(frm) {
        frm.set_df_property("status", "read_only", true);
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