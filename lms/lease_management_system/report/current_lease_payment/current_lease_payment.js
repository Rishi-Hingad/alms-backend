// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Current Lease Payment"] = {
	"filters": [

	],
	formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname == "payment_status") {
			if (value=="Paid"){
				return `<span style="background-color: #d4edda; color: #155724; display: block;">${value}</span>`;
			}
            else if(value=="Unpaid"){
				return `<span style="background-color: #f8d7da; color: #721c24; display: block;">${value}</span>`;
			}
        }

        return value;
    }
};
