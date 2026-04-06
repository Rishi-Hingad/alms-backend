frappe.listview_settings["Invoice Details"] = {
	onload: function (listview) {
		listview.page.add_inner_button("Fetch Details", function () {
			let d = new frappe.ui.Dialog({
				title: "Enter Batch Details",
				fields: [
					{
						label: "Batch Date",
						fieldname: "batch_date",
						fieldtype: "Date",
						reqd: 1,
					},
				],
				primary_action_label: "Submit",
				primary_action(values) {
					console.log(values);

					frappe.msgprint("Selected Date: " + values.batch_date);

					frappe.call({
						method: "leasemanagement.api.fetch_invoice_details.fetch_invoice",
						args: {
							batch_date: values.batch_date,
						},
						freeze: true,
						freeze_message: "Fetching Invoice Details...",
						callback: function (r) {
							console.log(r);

							if (r.message) {
								frappe.msgprint("Data fetched successfully");
							}
						},
					});

					d.hide();

					// call backend here
					// frappe.call({...})
				},
			});

			d.show();
		});
	},
};
