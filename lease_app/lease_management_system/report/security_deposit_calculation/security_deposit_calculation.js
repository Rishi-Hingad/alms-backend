// Copyright (c) 2026, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Security Deposit Calculation"] = {
	filters: [
		{
			fieldname: "lease_id",
			label: "Lease Agreement",
			fieldtype: "Link",
			options: "Lease Management",
			reqd: 1,
			get_query: function () {
				return {
					filters: {
						security_deposit: "Paid",
					},
				};
			},
		},
		// {
		//     "fieldname": "deposit_amount",
		//     "label": "Deposit Amount",
		//     "fieldtype": "Currency",
		//     // "reqd": 1
		// },
		// {
		//     "fieldname": "interest_rate",
		//     "label": "Interest Rate (%)",
		//     "fieldtype": "Float",
		//     // "reqd": 1
		// },
		// {
		//     "fieldname": "start_date",
		//     "label": "Start Date",
		//     "fieldtype": "Date",
		//     // "reqd": 1
		// },
		// {
		//     "fieldname": "end_date",
		//     "label": "End Date",
		//     "fieldtype": "Date",
		//     // "reqd": 1
		// }
	],
};
