// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

// frappe.ui.form.on("demo", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('demo', {
    // Trigger when first_name changes
    first_name: function(frm) {
        update_full_name(frm);
    },
    
    // Trigger when last_name changes
    last_name: function(frm) {
        update_full_name(frm);
    }
});

// Function to update the full_name field
function update_full_name(frm) {
    let full_name = frm.doc.first_name + " " + frm.doc.last_name; // Concatenate first and last name
    frm.set_value('full_name', full_name); // Dynamically set the value of full_name
}
