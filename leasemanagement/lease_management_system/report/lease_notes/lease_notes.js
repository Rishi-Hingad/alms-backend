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

				frappe.query_report.set_filter_value("prev_gross_immovable", null);
				frappe.query_report.set_filter_value("prev_gross_vehicle", null);
				frappe.query_report.set_filter_value("prev_acc_depre_immovable", null);
				frappe.query_report.set_filter_value("prev_acc_depre_vehicle", null);

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
		{
			fieldname: "prev_gross_immovable",
			fieldtype: "Float",
			hidden: 1,
		},
		{
			fieldname: "prev_gross_vehicle",
			fieldtype: "Float",
			hidden: 1,
		},
		{
			fieldname: "prev_acc_depre_immovable",
			fieldtype: "Float",
			hidden: 1,
		},
		{
			fieldname: "prev_acc_depre_vehicle",
			fieldtype: "Float",
			hidden: 1,
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

		// report.page.add_inner_button("Get Previous Year Data", () => {
		//     let company = frappe.query_report.get_filter_value("company_name");
		//     let year = frappe.query_report.get_filter_value("fin_start_year");

		//     // Validation
		//     if (!company || !year) {
		//         frappe.msgprint("Please select Company and Financial Start Year first.");
		//         return;
		//     }

		//     let prev_year = parseInt(year) - 1;

		//     frappe.call({
		//         method: "leasemanagement.api.utils.get_prev_notes_record",
		//         args: {
		//             company_name: company,
		//             fin_start_year: prev_year
		//         },
		//         callback: function (r) {
		//             if (r.message) {
		// 				frappe.query_report.set_filter_value("prev_gross_immovable", r.message.gross_immovable);
		// 				frappe.query_report.set_filter_value("prev_gross_vehicle", r.message.gross_vehicle);
		// 				frappe.query_report.set_filter_value("prev_acc_depre_immovable", r.message.acc_depre_immovable);
		// 				frappe.query_report.set_filter_value("prev_acc_depre_vehicle", r.message.acc_depre_vehicle);
		// 				frappe.msgprint("Previous year data loaded successfully.");
		// 				frappe.query_report.refresh();
		//                 // frappe.msgprint({
		//                 //     title: "Previous Year Data",
		//                 //     message: `
		//                 //         <b>Company:</b> ${company}<br>
		//                 //         <b>Year:</b> ${prev_year}<br><br>
		//                 //         Gross Immovable: ${r.message.gross_immovable}<br>
		//                 //         Gross Vehicle: ${r.message.gross_vehicle}<br>
		//                 //         Acc Depre Immovable: ${r.message.acc_depre_immovable}<br>
		//                 //         Acc Depre Vehicle: ${r.message.acc_depre_vehicle}
		//                 //     `,
		//                 //     indicator: "green"
		//                 // });
		//             }
		//         }
		//     });

		// });

		// report.page.add_inner_button("Get Previous Year Data", () => {

		// 	let company = frappe.query_report.get_filter_value("company_name");
		// 	let year = frappe.query_report.get_filter_value("fin_start_year");

		// 	if (!company || !year) {
		// 		frappe.msgprint("Please select Company and Financial Start Year first.");
		// 		return;
		// 	}

		// 	let prev_year = parseInt(year) - 1;

		// 	frappe.call({
		// 		method: "leasemanagement.api.utils.get_prev_notes_record",
		// 		args: {
		// 			company_name: company,
		// 			fin_start_year: prev_year
		// 		},
		// 		callback: function (r) {
		// 			if (r.message) {

		// 				let data = r.message;

		// 				// ✅ Show editable prompt with fetched values
		// 				frappe.prompt(
		// 					[
		// 						{
		// 							fieldname: "gross_immovable",
		// 							label: "Gross Immovable",
		// 							fieldtype: "Currency",
		// 							default: data.gross_immovable
		// 						},
		// 						{
		// 							fieldname: "gross_vehicle",
		// 							label: "Gross Vehicle",
		// 							fieldtype: "Currency",
		// 							default: data.gross_vehicle
		// 						},
		// 						{
		// 							fieldname: "acc_depre_immovable",
		// 							label: "Acc Depre Immovable",
		// 							fieldtype: "Currency",
		// 							default: data.acc_depre_immovable
		// 						},
		// 						{
		// 							fieldname: "acc_depre_vehicle",
		// 							label: "Acc Depre Vehicle",
		// 							fieldtype: "Currency",
		// 							default: data.acc_depre_vehicle
		// 						}
		// 					],
		// 					(values) => {

		// 						// ✅ Set hidden filters after user edits
		// 						frappe.query_report.set_filter_value("prev_gross_immovable", values.gross_immovable);
		// 						frappe.query_report.set_filter_value("prev_gross_vehicle", values.gross_vehicle);
		// 						frappe.query_report.set_filter_value("prev_acc_depre_immovable", values.acc_depre_immovable);
		// 						frappe.query_report.set_filter_value("prev_acc_depre_vehicle", values.acc_depre_vehicle);

		// 						frappe.msgprint("Previous year data applied successfully.");

		// 						// Refresh report
		// 						frappe.query_report.refresh();
		// 					},
		// 					"Review & Edit Previous Year Data",
		// 					"Apply"
		// 				);

		// 			}
		// 		}
		// 	});

		// });

		report.page.add_inner_button("Get Previous Year Data", () => {
			let company = frappe.query_report.get_filter_value("company_name");
			let year = frappe.query_report.get_filter_value("fin_start_year");

			if (!company || !year) {
				frappe.msgprint("Please select Company and Financial Start Year first.");
				return;
			}

			let prev_year = parseInt(year) - 1;

			let existing_data = {
				gross_immovable: frappe.query_report.get_filter_value("prev_gross_immovable"),
				gross_vehicle: frappe.query_report.get_filter_value("prev_gross_vehicle"),
				acc_depre_immovable: frappe.query_report.get_filter_value(
					"prev_acc_depre_immovable"
				),
				acc_depre_vehicle: frappe.query_report.get_filter_value("prev_acc_depre_vehicle"),
			};

			let already_set = Object.values(existing_data).some(
				(v) => v !== null && v !== undefined
			);

			function show_prompt(data, allow_refetch = false) {
				let dialog = new frappe.ui.Dialog({
					title: "Review & Edit Previous Year Data",
					fields: [
						{
							fieldname: "info",
							fieldtype: "HTML",
							options: `<b>Company:</b> ${company}<br><b>Year:</b> ${prev_year}<br><hr>`,
						},
						{
							fieldname: "gross_immovable",
							label: "Gross Amount Immovable",
							fieldtype: "Currency",
							default: data.gross_immovable,
						},
						{
							fieldname: "gross_vehicle",
							label: "Gross Amount Vehicle",
							fieldtype: "Currency",
							default: data.gross_vehicle,
						},
						{
							fieldname: "acc_depre_immovable",
							label: "Accumulated Amortization Immovable",
							fieldtype: "Currency",
							default: data.acc_depre_immovable,
						},
						{
							fieldname: "acc_depre_vehicle",
							label: "Accumulated Amortization Vehicle",
							fieldtype: "Currency",
							default: data.acc_depre_vehicle,
						},
					],
					primary_action_label: "Apply",
					primary_action(values) {
						frappe.query_report.set_filter_value(
							"prev_gross_immovable",
							values.gross_immovable
						);
						frappe.query_report.set_filter_value(
							"prev_gross_vehicle",
							values.gross_vehicle
						);
						frappe.query_report.set_filter_value(
							"prev_acc_depre_immovable",
							values.acc_depre_immovable
						);
						frappe.query_report.set_filter_value(
							"prev_acc_depre_vehicle",
							values.acc_depre_vehicle
						);

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

			if (already_set) {
				show_prompt(existing_data, true);
			} else {
				fetch_from_server();
			}
		});
	},
};
