// Copyright (c) 2026, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Lease Notes"] = {
	filters: [
		{
			fieldname: "company_name",
			label: "Company",
			fieldtype: "Link",
			options: "Company Master",
			reqd: 1,
		},
		{
			fieldname: "fin_start_year",
			label: "Financial Start Year",
			fieldtype: "Int",
			reqd: 1,
			on_change: function () {
				let start_year = frappe.query_report.get_filter_value("fin_start_year");

				if (!start_year) return;

				frappe.call({
					method: "leasemanagement.api.utils.auto_set_end_year",
					args: {
						start_year: start_year,
					},
					callback: function (r) {
						if (r.message) {
							frappe.query_report.set_filter_value("fin_end_year", r.message);
						}
					},
				});
			},
		},
		{
			fieldname: "fin_end_year",
			label: "Financial End Year",
			fieldtype: "Int",
			reqd: 1,
			read_only: 1,
		},
	],
	onload: function (report) {
		frappe.call({
			method: "leasemanagement.api.utils.get_financial_year",
			callback: function (r) {
				if (r.message) {
					frappe.query_report.set_filter_value("fin_start_year", r.message.start_year);
					frappe.query_report.set_filter_value("fin_end_year", r.message.end_year);
				}
			},
		});
		report.page.add_button(__("Download Excel"), function () {
			frappe.query_report.export_report();
		});
	},
};
