frappe.listview_settings['Invoice Details'] = {

    onload(listview) {

        listview.page.add_inner_button('Upload Invoice', () => {

            new frappe.ui.FileUploader({
                as_dataurl: false,
                allow_multiple: false,
                restrictions: {
                    allowed_file_types: ['.xlsx']
                },

                on_success(file) {

                    frappe.call({
                        method: "alms_app.crms.doctype.invoice_details.invoice_details.upload_invoice_excel",
                        args: {
                            file_url: file.file_url
                        },
                        freeze: true,
                        freeze_message: "Uploading Invoices...",

                        callback(r) {
                            if (r.message) {
                                frappe.msgprint(r.message);
                                listview.refresh();
                            }
                        }
                    });

                }

            });

        });

    }
};