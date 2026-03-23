// Copyright (c) 2025, Rishi Hingad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Car Process", {

    refresh(frm) {
        toggle_all_documents(frm);
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