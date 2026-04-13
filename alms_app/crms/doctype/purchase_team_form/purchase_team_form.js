let by_button = false;

/* ================================
   🔹 COMMON HELPERS
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
   🔹 STATUS BUTTON ENGINE
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

                    if (stage.field === "purchase_head_status") {
                        frm.set_value("status", values.action);
                    }

                    await frm.save();

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
   🔹 QUOTATION MODULE
================================ */

async function openQuotationDialog(frm) {
    const res = await frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Car Quotation",
            filters: { employee_details: frm.doc.name },
            fields: ["name", "finance_company", "status"]
        }
    });

    const data = res.message;
    if (!data.length) {
        frappe.msgprint("No quotations found.");
        return;
    }

    let html = data.map(q => `
        <div style="margin:10px;">
            <b>${q.finance_company}</b>
            <button class="btn btn-success btn-sm approve" data-id="${q.name}">✔</button>
            <button class="btn btn-danger btn-sm reject" data-id="${q.name}">✖</button>
        </div>
    `).join("");

    const d = new frappe.ui.Dialog({
        title: "Compare Quotations",
        fields: [{ fieldtype: "HTML", options: html }]
    });

    d.show();

    d.$wrapper.on("click", ".approve", async function () {
        const id = $(this).data("id");

        const { remarks } = await new Promise(resolve => {
            frappe.prompt([{ fieldname: "remarks", fieldtype: "Data", reqd: 1 }], resolve);
        });

        await frappe.call({
            method: "frappe.client.set_value",
            args: {
                doctype: "Car Quotation",
                name: id,
                fieldname: {
                    status: "Approved",
                    finance_team_remarks: remarks
                }
            }
        });

        await sendEmailSafe(frm.doc.name, "FinanceTeam To FinanceHead Payload", {
            quotation_id: id
        });

        frappe.msgprint("Approved");
        d.hide();
    });

    d.$wrapper.on("click", ".reject", async function () {
        const id = $(this).data("id");

        const { remarks } = await new Promise(resolve => {
            frappe.prompt([{ fieldname: "remarks", fieldtype: "Data", reqd: 1 }], resolve);
        });

        await frappe.call({
            method: "frappe.client.set_value",
            args: {
                doctype: "Car Quotation",
                name: id,
                fieldname: {
                    status: "Rejected",
                    finance_team_remarks: remarks
                }
            }
        });

        await sendEmailSafe(frm.doc.name, "Reject FinanceTeam to Vendor", {
            quotation_id: id
        });

        frappe.msgprint("Rejected");
        d.hide();
    });
}

/* ================================
   🔹 VENDOR EMAIL MODULE
================================ */

function addVendorButton(frm, role) {
    if (!["finance", "administrator"].includes(role)) return;

    const isApproved =
        frm.doc.purchase_team_status === "Approved" &&
        frm.doc.purchase_head_status === "Approved";

    const btn = frm.add_custom_button("Select Vendors", async () => {

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

                let selected = values.select_all
                    ? res.map(v => v.name)
                    : (values.vendors || []);

                if (!selected.length) {
                    frappe.msgprint("Select at least one vendor.");
                    return;
                }

                const btn = dialog.get_primary_btn();
                btn.prop("disabled", true).html("Sending...");

                try {
                    frappe.show_alert({
                        message: "Saving document...",
                        indicator: "blue"
                    });

                    await frm.save();

                    frappe.show_alert({
                        message: "Sending emails...",
                        indicator: "orange"
                    });

                    await sendEmailSafe(
                        frm.doc.name,
                        "FinanceHead To Quotation Company",
                        {
                            email_send_to: selected,
                            send_to_all: values.select_all ? 1 : 0
                        }
                    );

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
        /* ================================
        🔹 TOGGLE LOGIC (THE MAGIC)
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
        "background-color": isApproved ? "darkgreen" : "gray",
        "color": "white"
    });
}

/* ================================
   🔹 MAIN UI ENTRY
================================ */
function applyAdminOverrides(frm, role) {
    if (role === "administrator") {
        frm.set_df_property("purchase_team_status", "read_only", false);
        frm.set_df_property("purchase_head_status", "read_only", false);

        frm.set_df_property("purchase_team_remarks", "read_only", false);
        frm.set_df_property("purchase_head_remarks", "read_only", false);
    }
}

async function updateUI(frm) {

    const r = await getUserDesignation();
    const role = (r.message || "").trim().toLowerCase();
    frm.clear_custom_buttons();


    applyAdminOverrides(frm, role);

    buildStatusButtons(frm, role);

    if (["finance", "administrator", "finance head"].includes(role)) {
        frm.add_custom_button("Compare Quotations", () => openQuotationDialog(frm));
    }

    addVendorButton(frm, role);
}

/* ================================
   🔹 FORM EVENTS
================================ */

frappe.ui.form.on("Purchase Team Form", {
    refresh(frm) {
        updateUI(frm);
        calculateTotals(frm);
    },

    onload(frm) {
        frm.set_df_property("status", "read_only", true);
    }
});

/* ================================
   🔹 CALCULATIONS
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