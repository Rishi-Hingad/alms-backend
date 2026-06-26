// Copyright (c) 2025, Rishi Hingad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Car Process", {

    refresh(frm) {
        toggle_all_documents(frm);
        
        if (!frm.is_new()) {
            frm.add_custom_button(__("Resend Email"), () => {
                frappe.call({
                    method: "frappe.client.get",
                    args: {
                        doctype: "Car Process Config",
                        name: "Car Process Config"
                    },
                    callback: function(r) {
                        if (r.message && r.message.process_steps) {
                            let options = r.message.process_steps.map(step => step.form_name);
                            frappe.prompt([
                                {
                                    label: 'Select Form Step',
                                    fieldname: 'form_name',
                                    fieldtype: 'Select',
                                    options: options.join('\n'),
                                    reqd: 1
                                }
                            ], (values) => {
                                frappe.call({
                                    method: "alms_app.alms_app.api.car_process.resend_process_email",
                                    args: {
                                        car_process_name: frm.doc.name,
                                        form_name: values.form_name
                                    },
                                    callback: function(res) {
                                        if (!res.exc && res.message.status === "success") {
                                            frappe.msgprint(__("Email request for " + values.form_name + " sent successfully."));
                                        } else {
                                            frappe.msgprint({
                                                title: __("Error"),
                                                message: res.message.message || "An error occurred",
                                                indicator: "red"
                                            });
                                        }
                                    }
                                });
                            }, __("Resend Email"), __("Send"));
                        }
                    }
                });
            });
        }
    },

    po_received(frm) {
        toggle_all_documents(frm);
    },

    proforma_invoice_received(frm) {
        toggle_all_documents(frm);
    },

    insurance_copy_received(frm) {
        toggle_all_documents(frm);
    },

    rc_book_received(frm) {
        toggle_all_documents(frm);
    },

    payment_done(frm) {
        toggle_all_documents(frm);
    },

    registration_done(frm) {
        toggle_all_documents(frm);
    },

    car_delivery(frm) {
        toggle_all_documents(frm);
    },

    contract_signed(frm) {
        toggle_all_documents(frm);
    }

});


function toggle_all_documents(frm) {

    frm.toggle_display("po_document", frm.doc.po_received === "Yes");

    frm.toggle_display(
        "proforma_invoice_document",
        frm.doc.proforma_invoice_received === "Yes"
    );

    frm.toggle_display(
        "insurance_document",
        frm.doc.insurance_copy_received === "Yes"
    );

    frm.toggle_display(
        "rc_book_document",
        frm.doc.rc_book_received === "Yes"
    );

    frm.toggle_display(
        "payment_document",
        frm.doc.payment_done === "Yes"
    );

    frm.toggle_display(
        "registration_document",
        frm.doc.registration_done === "Yes"
    );

    frm.toggle_display(
        "agreement_document",
        frm.doc.car_delivery === "Yes"
    );

    frm.toggle_display(
        "contract_document",
        frm.doc.contract_signed === "Yes"
    );
}