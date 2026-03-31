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

		report.page.add_inner_button("Get Previous Year Data", () => {
			let company = frappe.query_report.get_filter_value("company_name");
			let year = frappe.query_report.get_filter_value("fin_start_year");

			if (!company || !year) {
				frappe.msgprint("Please select Company and Financial Start Year first.");
				return;
			}

			let prev_year = parseInt(year) - 1;

			// let existing_data = {
			// 	gross_immovable: frappe.query_report.get_filter_value("prev_gross_immovable"),
			// 	gross_vehicle: frappe.query_report.get_filter_value("prev_gross_vehicle"),
			// 	acc_depre_immovable: frappe.query_report.get_filter_value(
			// 		"prev_acc_depre_immovable"
			// 	),
			// 	acc_depre_vehicle: frappe.query_report.get_filter_value("prev_acc_depre_vehicle"),
			// };

			// let already_set = Object.values(existing_data).some(
			// 	(v) => v !== null && v !== undefined
			// );

			function show_prompt(data, allow_refetch = false) {
				let dialog = new frappe.ui.Dialog({
					title: "Review & Edit Previous Year Data",
					fields: [
						{
							fieldname: "info",
							fieldtype: "HTML",
							options: `<b>Company:</b> ${company}<br><b>Year:</b> ${prev_year} <br><b>Source:</b> ${
								data.from_saved ? "Saved Record" : "Auto Fetched"
							}<br>`,
						},
						{
							fieldtype: "Section Break",
						},
						{
							fieldname: "info",
							fieldtype: "HTML",
							options: `<b>Gross Carrying Amount</b> - <b>As at 1st April, ${prev_year}</b><br>`,
						},
						{
							fieldtype: "Section Break",
						},
						{
							fieldname: "gross_immovable",
							label: "Gross Amount Immovable",
							fieldtype: "Currency",
							default: data.gross_immovable,
						},
						{
							fieldtype: "Column Break",
						},
						{
							fieldname: "gross_vehicle",
							label: "Gross Amount Vehicle",
							fieldtype: "Currency",
							default: data.gross_vehicle,
						},
						{
							fieldtype: "Section Break",
						},
						{
							fieldname: "gross_add_immovable",
							label: "Gross Additions Immovable",
							fieldtype: "Currency",
							default: data.gross_add_immovable,
						},
						{
							fieldtype: "Column Break",
						},
						{
							fieldname: "gross_add_vehicle",
							label: "Gross Additions Vehicle",
							fieldtype: "Currency",
							default: data.gross_add_vehicle,
						},
						{
							fieldtype: "Section Break",
						},
						{
							fieldname: "gross_disposal_immovable",
							label: "Gross Disposals Immovable",
							fieldtype: "Currency",
							default: data.gross_disposal_immovable,
						},
						{
							fieldtype: "Column Break",
						},
						{
							fieldname: "gross_disposal_vehicle",
							label: "Gross Disposals Vehicle",
							fieldtype: "Currency",
							default: data.gross_disposal_vehicle,
						},
						{
							fieldtype: "Section Break",
						},
						{
							fieldname: "info",
							fieldtype: "HTML",
							options: `<b>Accumulated Amortization</b> - <b>As at 1st April, ${prev_year}</b><br>`,
						},
						{
							fieldtype: "Section Break",
						},
						{
							fieldname: "acc_depre_immovable",
							label: "Accumulated Amortization Immovable",
							fieldtype: "Currency",
							default: data.acc_depre_immovable,
						},
						{
							fieldtype: "Column Break",
						},
						{
							fieldname: "acc_depre_vehicle",
							label: "Accumulated Amortization Vehicle",
							fieldtype: "Currency",
							default: data.acc_depre_vehicle,
						},
						{
							fieldtype: "Section Break",
						},
						{
							fieldname: "acc_year_ended_immovable",
							label: "Accumulated Year Ended Immovable",
							fieldtype: "Currency",
							default: data.acc_year_ended_immovable,
						},
						{
							fieldtype: "Column Break",
						},
						{
							fieldname: "acc_year_ended_vehicle",
							label: "Accumulated Year Ended Vehicle",
							fieldtype: "Currency",
							default: data.acc_year_ended_vehicle,
						},
						{
							fieldtype: "Section Break",
						},
						{
							fieldname: "acc_dispoasal_immovable",
							label: "Accumulated Disposal Immovable",
							fieldtype: "Currency",
							default: data.acc_disposal_immovable,
						},
						{
							fieldtype: "Column Break",
						},
						{
							fieldname: "acc_disposal_vehicle",
							label: "Accumulated Disposal Vehicle",
							fieldtype: "Currency",
							default: data.acc_disposal_vehicle,
						},
					],
					primary_action_label: "Apply",
					primary_action(values) {
						// frappe.query_report.set_filter_value(
						// 	"prev_gross_immovable",
						// 	values.gross_immovable
						// );
						// frappe.query_report.set_filter_value(
						// 	"prev_gross_vehicle",
						// 	values.gross_vehicle
						// );
						// frappe.query_report.set_filter_value(
						// 	"prev_acc_depre_immovable",
						// 	values.acc_depre_immovable
						// );
						// frappe.query_report.set_filter_value(
						// 	"prev_acc_depre_vehicle",
						// 	values.acc_depre_vehicle
						// );

						// dialog.hide();
						// frappe.query_report.refresh();
						frappe.call({
							method: "leasemanagement.api.utils.upsert_previous_lease_details",
							args: {
								company: company,
								financial_start_year: prev_year,
								data: values,
							},
							callback: function (res) {
								// let msg = res.message === "updated"
								// 	? "Record Updated Successfully"
								// 	: "Record Created Successfully";

								// frappe.msgprint(msg);

								dialog.hide();
								frappe.query_report.refresh();
							},
						});
					},
				});
				if (allow_refetch) {
					dialog.add_custom_action("Refetch", () => {
						dialog.hide();
						fetch_from_server(); // force refetch
					});
				}

				dialog.show();
			}

			function fetch_from_server() {
				frappe.call({
					method: "leasemanagement.api.utils.get_prev_notes_record",
					args: {
						company_name: company,
						fin_start_year: prev_year,
					},
					callback: function (r) {
						if (r.message) {
							show_prompt(r.message, true);
						}
					},
				});
			}

			function fetch_data() {
				frappe.call({
					method: "leasemanagement.api.utils.get_previous_lease_details",
					args: {
						company: company,
						financial_start_year: prev_year,
					},
					callback: function (r) {
						if (r.message) {
							show_prompt(r.message, true);
						} else {
							fetch_from_server();
						}
					},
				});
			}

			// if (already_set) {
			// 	show_prompt(existing_data, true);
			// } else {
			// fetch_from_server();
			// }
			fetch_data();
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
