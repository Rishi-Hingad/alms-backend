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
					d.hide();

					frappe.call({
						method: "leasemanagement.api.fetch_invoice_details.fetch_invoice",
						args: {
							batch_date: values.batch_date,
						},
						freeze: true,
						freeze_message: "Fetching Invoice Details...",
						callback: function (r) {
							if (!r.message) {
								frappe.msgprint({
									title: "Error",
									message: "No response received from server.",
									indicator: "red",
								});
								return;
							}

							const res = r.message;

							// API-level error
							if (res.status === "Error") {
								frappe.msgprint({
									title: "Error",
									message: res.message || "Something went wrong.",
									indicator: "red",
								});
								return;
							}

							// No batches found
							if (!res.results || res.results.length === 0) {
								frappe.msgprint({
									title: "No Data",
									message: res.message || "No batches found for this date.",
									indicator: "orange",
								});
								return;
							}

							// Show per-batch result summary
							let summary = res.results
								.map((b) => {
									if (b.status === "Created") {
										return `✅ <b>${b.batch}</b>: Created — ${b.rows_added} row(s) added. [${b.docname}]`;
									} else if (b.status === "Updated") {
										return `<b>${b.batch}</b>: Updated — ${b.rows_added} new row(s) added. [${b.docname}]`;
									} else if (b.status === "No_Change") {
										return `<b>${b.batch}</b>: No change — all rows already exist. [${b.docname}]`;
									} else {
										return `❓ <b>${b.batch}</b>: ${b.status}`;
									}
								})
								.join("<br>");

							frappe.msgprint({
								title: "Fetch Complete",
								message: summary,
								indicator: "green",
							});

							// Refresh the list to show newly created records
							listview.refresh();
						},
					});
				},
			});

			d.show();
		});
	},
};
