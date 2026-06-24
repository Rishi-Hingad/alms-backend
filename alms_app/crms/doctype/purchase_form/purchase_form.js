// Copyright (c) 2026, Rishi Hingad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Form", {
    refresh: function(frm) {
        if (typeof window.setup_approval_ui === "function") {
            window.setup_approval_ui(frm);
        }
    },
    revised_ex_show_room_price: function(frm) { calculate_revised_fields(frm); },
    revised_discount: function(frm) { calculate_revised_fields(frm); },
    revised_tcs: function(frm) { calculate_revised_fields(frm); },
    revised_registration_charges: function(frm) { calculate_revised_fields(frm); },
    revised_accessories: function(frm) { calculate_revised_fields(frm); },
    kilometers_per_year: function(frm) { calculate_total_kilometers(frm); },
    tenure_in_years: function(frm) { calculate_total_kilometers(frm); }
});

function calculate_revised_fields(frm) {
    let ex_show_room = flt(frm.doc.revised_ex_show_room_price);
    let discount = flt(frm.doc.revised_discount);
    let tcs = flt(frm.doc.revised_tcs);
    let reg_charges = flt(frm.doc.revised_registration_charges);
    let accessories = flt(frm.doc.revised_accessories);

    let net_ex_show_room = ex_show_room - discount + tcs;
    let financed_amount = net_ex_show_room + reg_charges + accessories;

    frm.set_value("revised_net_ex_showroom_price", net_ex_show_room);
    frm.set_value("revised_financed_amount", financed_amount);
}

function calculate_total_kilometers(frm) {
    let km_per_year = flt(frm.doc.kilometers_per_year);
    let tenure = flt(frm.doc.tenure_in_years);
    
    if (km_per_year && tenure) {
        frm.set_value("total_kilometers", km_per_year * tenure);
    } else {
        frm.set_value("total_kilometers", "");
    }
}
