// Copyright (c) 2026, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.query_reports["Journal Entries Report"] = {
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
			default: get_financial_year().start_year,
			on_change: function () {
				auto_set_end_year();
			},
		},
		{
			fieldname: "fin_end_year",
			label: "Financial End Year",
			fieldtype: "Int",
			reqd: 1,
			read_only: 1,
			default: get_financial_year().end_year,
		},
	],
	onload: function (report) {
		auto_set_end_year();
		report.page.add_button(__("Download Excel"), function () {
			frappe.query_report.export_report();
		});
	},
};

function auto_set_end_year() {
	const start_year = frappe.query_report.get_filter_value("fin_start_year");

	if (!start_year) return;

	const end_year = parseInt(start_year) + 1;

	frappe.query_report.set_filter_value("fin_end_year", end_year);
}

function get_financial_year() {
	const today = frappe.datetime.get_today(); // yyyy-mm-dd
	const year = parseInt(today.split("-")[0]);
	const month = parseInt(today.split("-")[1]);

	if (month < 4) {
		return {
			start_year: year - 1,
			end_year: year,
		};
	} else {
		return {
			start_year: year,
			end_year: year + 1,
		};
	}
}
