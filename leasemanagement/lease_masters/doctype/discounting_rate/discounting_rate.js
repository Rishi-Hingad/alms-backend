// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Discounting Rate", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Discounting Rate", {
	discounting_rate: function (frm) {
		// Calculate new value
		let value1 = (1 + frm.doc.discounting_rate / 100) ** (1 / 365) - 1;
		let value2 = (1 + frm.doc.discounting_rate / 100) ** (1 / 12) - 1;

		// Set value in field2
		frm.set_value("daily_rate", value1);
		frm.set_value("monthly_rate", value2);
	},
});
