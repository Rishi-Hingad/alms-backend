// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Mismatch Invoice Amount"] = {
	// "filters": [

	// ]
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "taxable_amount") {
			// return `<span style="background-color: #d4edda; color: #155724; padding: 4px; border-radius: 4px; display: inline-block;">${value}</span>`;
			return `<span style="background-color: #d4edda; color: #155724; display: block;">${value}</span>`;
		}

		if (column.fieldname === "invoice_amount") {
			// return `<span style="background-color: #f8d7da; color: #721c24; padding: 4px; border-radius: 4px; display: inline-block;">${value}</span>`;
			return `<span style="background-color: #f8d7da; color: #721c24; display: block;">${value}</span>`;
		}

		return value;
	},
};
