// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Property Master", {
	type_of_asset: function (frm) {
		if (frm.doc.type_of_asset == "Property") {
			frm.set_df_property("city", "reqd", 1);
			frm.set_df_property("area_sq_ft", "reqd", 1);
			frm.set_df_property("address", "reqd", 1);
		}
	},
});
