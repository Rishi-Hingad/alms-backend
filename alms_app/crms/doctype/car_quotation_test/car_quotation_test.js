// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt
frappe.ui.form.on('Car Quotation Test', {
    attach_file: function(frm) {
        if (frm.doc.attach_file) {
            frappe.call({
                method: "alms_app.crms.doctype.car_quotation_test.car_quotation_test.process_file",
                args: { file_url: frm.doc.attach_file },
                callback: function(r) {
                    if (r.message) {
                        // Populate fields with data from the backend
                        frm.set_value('location', r.message.location);
                        frm.set_value('kms', r.message.kms);
                        frm.set_value('variant', r.message.variant);
                        // Set other fields as required

                        // Show hidden fields
                        frm.fields_dict.location.df.hidden = 0;
                        frm.fields_dict.kms.df.hidden = 0;
                        frm.fields_dict.variant.df.hidden = 0;
                        frm.refresh_field('location');
                        frm.refresh_field('kms');
                        frm.refresh_field('variant');
                    }
                }
            });
        }
    }
});
