frappe.listview_settings['Invoice Batch'] = {

    onload(listview) {

        listview.page.add_inner_button('Upload Invoice', () => {

            let dialog = new frappe.ui.Dialog({
                title: 'Select Vendor',
                fields: [
                    {
                        label: 'Vendor Company',
                        fieldname: 'vendor',
                        fieldtype: 'Select',
                        options: ['Eazy Assets', 'ALD'],
                        reqd: 1
                    }
                ],
                primary_action_label: 'Next',
                primary_action(values) {

                    dialog.hide();

                    // Open file uploader AFTER vendor selection
                    new frappe.ui.FileUploader({
                        as_dataurl: false,
                        allow_multiple: false,
                        restrictions: {
                            allowed_file_types: ['.xlsx']
                        },

                        on_success(file) {

                            frappe.call({
                                method: "lease_app.crms.doctype.invoice_details.invoice_details.upload_invoice_excel",
                                args: {
                                    file_url: file.file_url,
                                    vendor: values.vendor,
                                    user_email: frappe.session.user
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
                }
            });

            dialog.show();
        });
    }
};