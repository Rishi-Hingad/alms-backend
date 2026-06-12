// Copyright (c) 2026, Rishi Hingad and contributors
// For license information, please see license.txt

function is_admin() {
    return frappe.session.user === "Administrator";
}

function has_role(role) {
    return frappe.user_roles.includes(role) || is_admin();
}



frappe.ui.form.on("Invoice Batch", {
    onload(frm) {
        if (window.setup_approval_ui) {
            window.setup_approval_ui(frm);
        }
    },
    refresh(frm) {
        if (window.setup_approval_ui) {
            window.setup_approval_ui(frm);
        }

        if (frm.doc.excel_file) {
            if (frm.doc.status === "Pending" || frm.doc.status === "Failed") {

                frm.add_custom_button("Retry Failed Rows", () => {
                    frappe.call({
                        method: "alms_app.crms.doctype.invoice_batch.invoice_batch.retry_failed",
                        args: {
                            docname: frm.doc.name
                        },
                        callback: function (r) {
                            if (r.message) {
                                frappe.msgprint(r.message.message || "Done");
                            }
                            frm.reload_doc();
                        }
                    })
                })

                frm.add_custom_button("Download Error Report", () => {
                    window.open(
                        `/api/method/alms_app.crms.doctype.invoice_batch.invoice_batch.download_error_report?docname=${frm.doc.name}`
                    )
                })
            }
        }
    }
});

frappe.ui.form.on('Invoice Batch', {

    render_pdf_preview: function (frm, attachment_field, preview_field) {

        let file_url = frm.doc[attachment_field];

        if (!file_url) {
            frm.set_df_property(preview_field, 'options', '');
            frm.refresh_field(preview_field);
            return;
        }

        if (!file_url.toLowerCase().includes(".pdf")) {
            frm.set_df_property(preview_field, 'options',
                `<p style="color:red;">Preview not available</p>`
            );
            frm.refresh_field(preview_field);
            return;
        }

        frappe.call({
            method: "alms_app.crms.doctype.invoice_batch.invoice_batch.get_file_preview_url",
            args: {
                file_url: file_url
            },
            callback: function (r) {
                if (r.message) {

                    let html = `
                        <div style="width: 100%; height: 600px;">
                            <iframe 
                                src="${r.message}" 
                                width="100%" 
                                height="100%"
                                style="border:none;">
                            </iframe>
                        </div>
                    `;

                    frm.set_df_property(preview_field, 'options', html);
                    frm.refresh_field(preview_field);
                }
            }
        });
    },

    invoice_attachment: function (frm) {
        frm.events.render_pdf_preview(frm, 'invoice_attachment', 'file_preview');
    },

    invoice_attachment_1: function (frm) {
        frm.events.render_pdf_preview(frm, 'invoice_attachment_1', 'file_preview_1');
    },

    refresh: function (frm) {
        frm.events.render_pdf_preview(frm, 'invoice_attachment', 'file_preview');
        frm.events.render_pdf_preview(frm, 'invoice_attachment_1', 'file_preview_1');
    }

});

frappe.ui.form.on('Invoice Batch', {
    refresh(frm) {

        // Show button only if API failed AND conditions are valid
        if (
            frm.doc.hr_head_status === "Approved" &&
            frm.doc.status === "Completed" &&
            !frm.doc.lease_api_call
        ) {
            frm.add_custom_button("Retry API", () => {

                frappe.call({
                    method: "alms_app.crms.doctype.invoice_batch.invoice_batch.retry_lease_api",
                    args: {
                        docname: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Retrying API call..."
                }).then(r => {
                    frappe.msgprint(r.message.message || "Done");
                    frm.reload_doc();
                });

            }).addClass("btn-primary");
        }
    }
});