// Copyright (c) 2026, Meril and contributors
// For license information, please see license.txt

frappe.ui.form.on("RE KR Entry", {
	refresh(frm) {
		// Show outdated banner if this record is superseded
		if (frm.doc.is_outdated) {
			frm.dashboard.add_comment(
				__("⚠️ This record is outdated. A newer version was fetched from SAP."),
				"red",
				true
			);
		}
	},
});
