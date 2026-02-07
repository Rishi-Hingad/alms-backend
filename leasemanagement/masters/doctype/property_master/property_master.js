// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Property Master", {
	before_save(frm) {
		if (frm.doc.type_of_asset == "Car") {
			frm.set_value("address", frm.doc.employee);
		}
	},
});
