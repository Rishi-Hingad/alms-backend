// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Lease Payment"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": "Month",
			"fieldtype": "Select",
			"options": "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
			"reqd": 1
		},
		{
			"fieldname": "year",
			"label": "Year",
			"fieldtype": "Int",
			"default": frappe.datetime.get_today().split("-")[0],
			"reqd": 1
		}
	]
};
