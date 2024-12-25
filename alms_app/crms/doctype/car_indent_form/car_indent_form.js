// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Car Indent Form", {
    refresh(frm) {
        calculate_totals(frm);
    },

    ex_showroom_price: function(frm) {
        calculate_totals(frm);
    },

    discount: function(frm) {
        calculate_totals(frm);
    },

    tcs: function(frm) {
        calculate_totals(frm);
    },

    registration_charges: function(frm) {
        calculate_totals(frm);
    },

    accessories: function(frm) {
        calculate_totals(frm);
    }
});

function calculate_totals(frm) {
    const ex_showroom_price = frm.doc.ex_showroom_price || 0;
    const discount = frm.doc.discount || 0;
    const tcs = frm.doc.tcs || 0;
    const registration_charges = frm.doc.registration_charges || 0;
    const accessories = frm.doc.accessories || 0;

    frm.set_value("net_ex_showroom_price", ex_showroom_price - discount + tcs);

    const finance_amount = (ex_showroom_price - discount + tcs) + registration_charges + accessories;
    frm.set_value("finance_amount", finance_amount);
}