// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Lease Report Monthly (Without Escalation)"] = {
	filters: [
		{
			fieldname: "docname",
			label: "Lease Agreement",
			fieldtype: "Link",
			options: "Lease Management",
			reqd: 1,
			get_query: function () {
				return {
					filters: {
						calculation_rate_type: "Monthly Rate",
						lease_period: "Short Term (Less Than 12 Months)",
					},
				};
			},
		},
	],
	onload: function (report) {
		report.page.add_button(__("Download Excel"), function () {
			frappe.query_report.export_report();
		});
	},
};
