// Copyright (c) 2026, Rishi Hingad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice Import", {
    refresh(frm) {

        if (frm.doc.excel_file) {

            frm.add_custom_button("Parse Excel", () => {
                frappe.call({
                    method: "alms_app.crms.doctype.invoice_import.invoice_import.parse_excel",
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
                    method: "alms_app.crms.doctype.invoice_import.invoice_import.process_rows",
                    args: {
                        docname: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Processing invoices..."
                })
            })


            frm.add_custom_button("Retry Failed Rows", () => {
                frappe.call({
                    method: "alms_app.crms.doctype.invoice_import.invoice_import.retry_failed",
                    args: {
                        docname: frm.doc.name
                    }
                })
            })

            frm.add_custom_button("Download Error Report", () => {

                window.open(
                    `/api/method/alms_app.crms.doctype.invoice_import.invoice_import.download_error_report?docname=${frm.doc.name}`
                )

            })
        }
    }
});