// Copyright (c) 2026, Rishi Hingad and contributors
// For license information, please see license.txt

function is_admin() {
    return frappe.session.user === "Administrator";
}

function has_role(role) {
    return frappe.user_roles.includes(role) || is_admin();
}

const APPROVALS = [
    {
        role: "Finance Team",
        field: "finance_team",
        status_field: "finance_team_status",
        depends_on: null
    },
    {
        role: "Finance Head",
        field: "finance_head",
        status_field: "finance_head_status",
        depends_on: "finance_team_status"
    },
    {
        role: "HR Head",
        field: "hr_head",
        status_field: "hr_head_status",
        depends_on: "finance_head_status"
    }
];

function get_button_class(status) {
    if (status === "Approved") return "btn-approved";
    if (status === "Rejected") return "btn-rejected";
    return "btn-pending";
}

frappe.ui.form.on("Invoice Batch", {
    refresh(frm) {

        if (frm.doc.excel_file) {
            if (frm.doc.status === "Pending" || frm.doc.status === "Failed") {
                frm.add_custom_button("Parse Excel", () => {
                    frappe.call({
                        method: "alms_app.crms.doctype.invoice_batch.invoice_batch.parse_excel",
                        args: {
                            docname: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: "Reading Excel..."
                    }).then(() => {
                        frm.reload_doc()
                    })
                })


                frm.add_custom_button("Process Rows", () => {
                    frappe.call({
                        method: "alms_app.crms.doctype.invoice_batch.invoice_batch.process_rows",
                        args: {
                            docname: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: "Processing invoices..."
                    })
                })


                frm.add_custom_button("Retry Failed Rows", () => {
                    frappe.call({
                        method: "alms_app.crms.doctype.invoice_batch.invoice_batch.retry_failed",
                        args: {
                            docname: frm.doc.name
                        }
                    })
                })

                frm.add_custom_button("Download Error Report", () => {

                    window.open(
                        `/api/method/alms_app.crms.doctype.invoice_batch.invoice_batch.download_error_report?docname=${frm.doc.name}`
                    )

                })
            }

            if (frm.doc.status === "Completed") {

                APPROVALS.forEach(cfg => {

                    const status = frm.doc[cfg.status_field] || "Pending";
                    let showButton = false;
                    // ================= ADMIN ================= //
                    if (is_admin()) {
                        showButton = true;
                    }
                    // ================= NORMAL USERS ================= //
                    else {
                        const hasAccess = has_role(cfg.role);
                        const isPending = status === "Pending";

                        let dependencyOk = true;
                        if (cfg.depends_on) {
                            dependencyOk = frm.doc[cfg.depends_on] === "Approved";
                        }
                        if (hasAccess && dependencyOk) {
                            showButton = true;
                        }
                    }

                    if (showButton) {

                        let btn = frm.add_custom_button(
                            `${cfg.role}: ${status}`,
                            () => {
                                if (status !== "Pending") {
                                    frappe.msgprint(`${cfg.role} already ${status}`);
                                    return;
                                }
                                open_approval_dialog(frm, cfg.field, cfg.role);
                            }
                        );

                        btn.removeClass("btn-default");

                        btn.addClass(get_button_class(status));

                        if (status !== "Pending") {
                            btn.prop("disabled", true);
                        }
                    }

                });
            }

        }
    }
});

function open_approval_dialog(frm, role_field, role_label) {

    let d = new frappe.ui.Dialog({
        title: `${role_label} Action`,
        fields: [
            {
                label: "Action",
                fieldname: "action",
                fieldtype: "Select",
                options: ["Approved", "Rejected"],
                reqd: 1
            },
            {
                label: "Remarks",
                fieldname: "remarks",
                fieldtype: "Data",
                reqd: 1
            }
        ],
        primary_action_label: "Submit",
        primary_action(values) {

            frappe.call({
                method: "alms_app.crms.doctype.invoice_batch.invoice_batch.update_approval_status",
                args: {
                    docname: frm.doc.name,
                    role: role_field,
                    action: values.action,
                    remarks: values.remarks
                },
                freeze: true,
                freeze_message: "Updating..."
            }).then(() => {
                d.hide();
                frm.reload_doc();
            });
        }
    });

    d.show();
}