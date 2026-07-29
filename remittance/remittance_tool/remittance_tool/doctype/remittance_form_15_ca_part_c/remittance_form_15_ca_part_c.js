// Copyright (c) 2026, Saurabh Tiwari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Remittance Form 15 CA Part_C", {
	// refresh(frm) {

	// },
	dtaa_name: function (frm) {
		if (frm.doc.dtaa_name) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "DTAA Master",
					name: frm.doc.dtaa_name,
				},
				callback: function (r) {
					if (r.message) {
						let options = [];

						r.message.articles.forEach(function (row) {
							if (row.enabled) {
								options.push(row.article_no + " - " + row.article_description);
							}
						});

						frm.set_df_property("dtaa_article", "options", options.join("\n"));

						frm.refresh_field("dtaa_article");
					}
				},
			});
		}
	},
});
