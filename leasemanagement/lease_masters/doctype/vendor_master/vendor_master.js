// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vendor Master", {
	// refresh: function (frm) {
	// frm.set_query("pin_code", function () {
	// return {
	//     filters: {
	//     city: frm.doc.city
	//     }
	// };
	// });

	// }
	pin_code: function (frm) {
		if (frm.doc.pin_code) {
			frappe.db
				.get_doc("Pincode Master", frm.doc.pin_code)
				.then((doc) => {
					// Assuming the fieldname in Vendor Master is 'city' (not 'City')
					frm.set_value("city", doc.city);
				})
				.catch(() => {
					frappe.msgprint(__("Pincode not found in Pincode Master"));
					frm.set_value("city", "");
				});
		} else {
			// Clear city if pin_code is cleared
			frm.set_value("city", "");
		}
	},
});
// frappe.ui.form.on('Vendor Master', {
//     city: function(frm) {
//         if (frm.doc.city_name) {
//             frappe.call({
//                 method: 'frappe.client.get',
//                 args: {
//                     doctype: 'Pincode Master',
//                     filters: { 'city': frm.doc.city_name },
//                     fieldname: ['pin_code']
//                 },
//                 callback: function(r) {
//                     if (r.message) {
//                         frm.set_value('pin_code', r.message.pin_code);
//                     }
//                 }
//             });
//         }
//     }
// });
