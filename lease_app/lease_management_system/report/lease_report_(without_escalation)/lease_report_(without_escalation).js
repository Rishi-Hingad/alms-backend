// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Lease Report (Without Escalation)"] = {
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
						calculation_rate_type: "Daily Rate",
						lease_period: "Short Term (Less Than 12 Months)",
					},
				};
			},
		},
	],
};
