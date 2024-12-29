// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt


function addButtonForAppovel(frm){
    frm.clear_custom_buttons();
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "User",
            name: frappe.session.user, // Current logged-in user
        },
        callback: function (response) {
            if (response && response.message) {
                const designation = response.message.designation;
                
                if (designation === "Purchase"){
                    frm.set_df_property('status','read_only', 1)
                    
                }
                if ((designation === "Purchase Head") || (designation === "Admin")){
                    frm.add_custom_button("Appove by Purchase Head",null)
                }
            }}
        })
}

frappe.ui.form.on("Purchase Team Form", {
        refresh(frm) {
            calculate_totals(frm);
            addButtonForAppovel(frm);
        },
        onload(frm){
            addButtonForAppovel(frm); 
        },
    
        revised_ex_show_room_price: function(frm) {
            calculate_totals(frm);
        },
    
        revised_discount: function(frm) {
            calculate_totals(frm);
        },
    
        revised_tcs: function(frm) {
            calculate_totals(frm);
        },
    
        revised_registration_charges: function(frm) {
            calculate_totals(frm);
        },
    
        revised_accessories: function(frm) {
            calculate_totals(frm);
        },

        kilometers_per_year: function(frm) {
            calculate_totals(frm);
        },

        tenure_in_years: function(frm) {
            calculate_totals(frm);
        }
});

function calculate_totals(frm) {
    const revised_ex_show_room_price = frm.doc.revised_ex_show_room_price || 0;
    const revised_tcs = frm.doc.revised_tcs || 0;
    const revised_accessories = frm.doc.revised_accessories || 0;
    const revised_discount = frm.doc.revised_discount || 0;
    const revised_registration_charges = frm.doc.revised_registration_charges || 0;
    const kilometers_per_year = frm.doc.kilometers_per_year || 0;
    const tenure_in_years = frm.doc.tenure_in_years || 0;

    frm.set_value("total_kilometers", kilometers_per_year * tenure_in_years);

    const revised_net_ex_showroom_price = revised_ex_show_room_price + revised_tcs - revised_discount;
    frm.set_value("revised_net_ex_showroom_price", revised_net_ex_showroom_price);

    const finance_amount = (revised_ex_show_room_price + revised_tcs - revised_discount) + revised_accessories + revised_registration_charges;
    frm.set_value("revised_financed_amount", finance_amount);
}

