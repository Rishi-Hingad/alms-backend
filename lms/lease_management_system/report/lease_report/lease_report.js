// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Lease Report"] = {
	"filters": [
			{
				"fieldname": "docname",
				"label": "Lease Agreement",
				"fieldtype": "Link",
				"options": "Lease Management",
				"reqd": 1
			}
		]

};