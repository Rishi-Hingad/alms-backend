// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Escalation", {
	escalation_type: function (frm, cdt, cdn) {
		auto_set_start_end_date_escalation(frm, cdt, cdn);
	},
	start_date: function (frm, cdt, cdn) {
		validate_escalation_dates(frm, cdt, cdn);
	},
	end_date: function (frm, cdt, cdn) {
		validate_escalation_dates(frm, cdt, cdn);
	},
});
frappe.ui.form.on("Additional Amounts", {
	start_date: function (frm, cdt, cdn) {
		validate_additional_dates(frm, cdt, cdn);
	},
	end_date: function (frm, cdt, cdn) {
		validate_additional_dates(frm, cdt, cdn);
	},
});
frappe.ui.form.on("Invoice Documents", {
	from_date: function (frm, cdt, cdn) {
		validate_from_to_dates(frm, cdt, cdn);
		update_custom_row_id(frm, cdt, cdn);
	},
	to_date: function (frm, cdt, cdn) {
		validate_from_to_dates(frm, cdt, cdn);
		update_custom_row_id(frm, cdt, cdn);
	},
	manage_attachments: function (frm, cdt, cdn) {
		if (frm.is_new()) {
			frappe.msgprint(__("Save the document before adding attachments."));
			return;
		}
		const row = locals[cdt][cdn];
		// gather current attachments for this invoice-row
		const att = (frm.doc.invoice_attachments || []).filter(
			(a) => a.invoice_row === row.custom_row_id
		);
		// Dialog to show attachments and upload new ones
		const dialog = new frappe.ui.Dialog({
			title: `Attachments for ${frappe.datetime.str_to_user(
				row.from_date
			)} to ${frappe.datetime.str_to_user(row.to_date)}`,

			fields: [{ fieldtype: "HTML", fieldname: "attachment_list" }],
			primary_action_label: "Upload file(s)",
			primary_action: function () {
				new frappe.ui.FileUploader({
					allow_multiple: 1,
					doctype: frm.doctype,
					docname: frm.doc.name,
					folder: "Home/Attachments",
					on_success: (file) => {
						// file is a single File doc
						const new_child = frm.add_child("invoice_attachments");
						new_child.file = file.file_url;
						new_child.file_docname = file.name;
						new_child.invoice_row = row.custom_row_id;
						new_child.uploaded_by = frappe.session.user;
						new_child.uploaded_on = frappe.datetime.now_datetime();

						frm.refresh_field("invoice_attachments");
						dialog.hide();
					},
					onerror: (err) => {
						frappe.msgprint(__("Upload failed: {0}", [err]));
					},
				});
			},
		});

		dialog.show();

		frappe.call({
			method: "leasemanagement.lease_management_system.doctype.lease_management.lease_management.get_invoice_attachments",
			args: {
				filters: {
					parent: frm.doc.name,
					parenttype: frm.doctype,
					invoice_row: row.custom_row_id,
				},
			},
			callback: function (r) {
				const $wrapper = dialog.fields_dict.attachment_list.$wrapper.empty();
				const attachments = r.message || [];

				if (!attachments.length) {
					$wrapper.html('<div class="text-muted">No attachments yet</div>');
					return;
				}
				const $table = $(`
                    <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                        <table class="table  table-hover table-bordered align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th style="min-width: 200px;">File</th>
                                    <th style="min-width: 150px;">Uploaded By</th>
                                    <th style="min-width: 160px;">Uploaded On</th>
                                    <th style="width: 100px; text-align: center;">Action</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                `);

				attachments.forEach((a) => {
					const filename = a.file.split("/").pop();
					const row = `
                        <tr>
                            <td><a href="${a.file}" target="_blank">${filename}</a></td>
                            <td>${a.uploaded_by}</td>
                            <td>${frappe.datetime.str_to_user(a.uploaded_on)}</td>
                            <td class="text-center">
                                <a class="text-danger" style="cursor:pointer;" data-name="${
									a.name
								}" title="Delete">
                                    <i class="fa fa-trash"></i>
                                </a>
                            </td>
                        </tr>
                    `;
					$table.find("tbody").append(row);
				});

				$wrapper.append($table);

				// Hook delete clicks
				$wrapper.on("click", "a[data-name]", function () {
					const name = $(this).attr("data-name");
					frappe.confirm(__("Delete this attachment?"), () => {
						frappe.call({
							method: "leasemanagement.lease_management_system.doctype.lease_management.lease_management.delete_invoice_attachment",
							args: {
								parent_doctype: frm.doctype,
								parent_name: frm.doc.name,
								attachment_name: name,
								delete_file: false,
							},
							callback: function (r) {
								if (r.message === "ok") {
									frm.reload_doc(); // reload whole doc so UI is in sync
									dialog.hide();
								}
							},
						});
					});
				});
			},
		});
	},
});

frappe.ui.form.on("Lease Management", {
	vendor: function (frm) {
		if (frm.doc.vendor) {
			// Set property filter based on selected vendor
			frm.set_query("property_description", function () {
				return {
					filters: {
						vendor: frm.doc.vendor,
					},
				};
			});

			// frm.set_query("car_description", function () {
			// 	return {
			// 		filters: {
			// 			vendor: frm.doc.vendor,
			// 		},
			// 	};
			// });
		} else {
			// Clear property field if vendor is cleared
			frm.set_value("property_description", null);
			// frm.set_value("car_description", null);

			// Remove query filter
			// frm.set_query("car_description", function () {
			// 	return {
			// 		filters: {
			// 			name: null, // Will return no property
			// 		},
			// 	};
			// });
		}
	},
	car_description: function (frm) {
		if (frm.doc.car_description) {
			frappe.db
				.get_value("Car Description Master", { name: frm.doc.car_description }, [
					"company",
					"vendor",
				])
				.then((r) => {
					if (r.message) {
						frm.set_value("company", r.message.company);
						frm.set_value("vendor", r.message.vendor);
					}
				});
		} else {
			frm.set_value("company", null);
			frm.set_value("vendor", null);
		}
	},
	agreement_start_date: function (frm) {
		validate_dates_and_set_lease_period(frm);
	},
	agreement_end_date: function (frm) {
		validate_dates_and_set_lease_period(frm);
	},
	onload_post_render(frm) {
		if (
			frm.doc.invoice_details &&
			frm.doc.invoice_details.length > 0 &&
			(frappe.user.has_role("Accounts") || frappe.user.has_role("System Manager"))
		) {
			highlight_mismatched_rows(frm);
		}
	},
	onload(frm) {
		// if(!frm.doc.is_modified){
		// 	set_agreement_status(frm);
		// }
		if (!frm.doc.vendor) {
			frm.set_query("property_description", function () {
				return {
					filters: {
						name: null, // blocks all results
					},
				};
			});
			// frm.set_query("car_description", function () {
			// 	return {
			// 		filters: {
			// 			name: null, // blocks all results
			// 		},
			// 	};
			// });
		}

		frm.report_counter = 0;

		const user_roles = frappe.user_roles;

		if (
			user_roles.includes("Vendor") &&
			!user_roles.includes("System Manager") &&
			!user_roles.includes("Accounts")
		) {
			frappe.meta.get_docfield(
				"Invoice Documents",
				"payment_status",
				frm.doc.name
			).hidden = 1;
		}

		if (
			(frappe.user.has_role("Vendor") || frappe.user.has_role("Accounts")) &&
			!frappe.user.has_role("System Manager")
		) {
			if (frm.doc.status == "Terminated") {
				set_lease_fields_readonly(frm);
			}
		}
	},
	refresh: function (frm) {
		frm.page.set_indicator(__(frm.doc.status), get_status_color(frm.doc.status));
		// frm.dashboard.clear_headline();

		// // ── Root/Original Lease ─────────────────────────────────────
		// if (!frm.doc.parent_lease && !frm.doc.is_modified) {
		// 	frm.dashboard.set_headline(
		// 		`<span class="indicator-pill green">Parent Lease</span>`
		// 	);
		// }

		// // ── Modified/Child Lease ────────────────────────────────────
		// if (frm.doc.parent_lease) {
		// 	frm.dashboard.set_headline(
		// 		`<span class="indicator-pill orange">
		// 			Modified Lease — Version ${frm.doc.modification_version}
		// 			| Parent: ${frm.doc.parent_lease}
		// 		</span>`
		// 	);
		// }
		if (
			frappe.user.has_role("Vendor") &&
			!frappe.user.has_role("System Manager") &&
			!frappe.user.has_role("Accounts")
		) {
			frm.add_custom_button(__("Add Invoice Entry"), function () {
				open_invoice_dialog();
			});
		}

		if (
			frm.doc.invoice_details &&
			frm.doc.invoice_details.length > 0 &&
			(frappe.user.has_role("Accounts") || frappe.user.has_role("System Manager"))
		) {
			highlight_mismatched_rows(frm);
		}

		if (frappe.user.has_role("Vendor")) {
			frm.fields_dict.invoice_details.grid.df.read_only = 0;
			frm.fields_dict.invoice_details.grid.refresh();
		}
		if (!frm.doc.discounting_rate && frm.is_new()) {
			frappe.db
				.get_list("Discounting Rate", {
					limit: 1,
					order_by: "creation asc",
					fields: ["name", "discounting_rate"],
				})
				.then((records) => {
					if (records.length > 0) {
						const first_record = records[0];
						frm.set_value("discounting_rate", first_record.discounting_rate);
					} else {
						frappe.msgprint(__("No records found."));
					}
				});
		}

		// frm.set_query("property_description", function () {
		// return {
		//     filters: {
		//     vendor: frm.doc.vendor
		//     }
		// }});

		if (!frm.is_new()) {
			if (frappe.user.has_role("Accounts") || frappe.user.has_role("System Manager")) {
				// frm.add_custom_button(__("Generate Report"), function () {
				// 	frm.report_counter = (frm.report_counter || 0) + 1;
				// 	frappe.call({
				// 		method: "leasemanagement.lease_management_system.doctype.lease_management.lease_management.generate_report",
				// 		args: {
				// 			docname: frm.doc.name,
				// 			cnt: frm.report_counter,
				// 		},
				// 		callback: function (r) {
				// 			if (!r.exc) {
				// 				let file_url = r.message.file_url;
				// 				// frappe.msgprint("mes"+r.message);
				// 				window.open(file_url);
				// 			} else {
				// 				frappe.msgprint(__("Failed to generate report."));
				// 			}
				// 		},
				// 	});
				// });
				if (frm.doc.status == "Active" || frm.doc.status == "Modified") {
					frm.add_custom_button(__("Terminate Lease"), function () {
						frappe.confirm("Are you sure you want to terminate this lease?", () => {
							let d = new frappe.ui.Dialog({
								title: "Terminate Lease",
								fields: [
									{
										label: "Termination Date",
										fieldname: "termination_date",
										fieldtype: "Date",
										reqd: 1,
									},
									{
										label: "Termination Reason",
										fieldname: "termination_reason",
										fieldtype: "Small Text",
										reqd: 1,
									},
								],
								primary_action_label: "Terminate",
								primary_action(values) {
									let termination_date = frappe.datetime.str_to_obj(
										values.termination_date
									);
									let start_date = frappe.datetime.str_to_obj(
										frm.doc.agreement_start_date
									);
									let end_date = frappe.datetime.str_to_obj(
										frm.doc.agreement_end_date
									);

									if (
										termination_date < start_date ||
										termination_date > end_date
									) {
										frappe.msgprint(
											__(
												"Termination Date must be between Agreement Start Date and Agreement End Date"
											)
										);
										return;
									}
									frappe.call({
										method: "frappe.client.set_value",
										args: {
											doctype: "Lease Management",
											name: frm.doc.name,
											fieldname: {
												termination_date: values.termination_date,
												termination_reason: values.termination_reason,
												status: "Terminated",
											},
										},
										callback: function () {
											frappe.msgprint("Lease Terminated Successfully");
											frm.reload_doc();
										},
									});

									d.hide();
								},
							});

							d.show();
						});
					}).addClass("btn-danger");
				}

				if (
					frm.doc.status == "Active" ||
					frm.doc.status == "Modified" ||
					frm.doc.status == "Agreement Expired"
				) {
					frm.add_custom_button(__("Modify Agreement"), function () {
						// frappe.new_doc("Lease Management", {
						// 	previous_lease:frm.doc.name,
						// 	parent_lease:frm.doc.name,
						// 	is_modified: 1,
						// 	status:"Modified",
						// });
						let new_doc = frappe.model.copy_doc(frm.doc);

						new_doc.agreement_start_date = null;
						new_doc.agreement_end_date = null;
						new_doc.monthly_rent = null;
						new_doc.modification_reason = null;
						new_doc.previous_wdv = 0;

						new_doc.modifications = [];
						new_doc.invoice_details = [];
						new_doc.invoice_attachments = [];
						new_doc.escalation = [];
						new_doc.additional_amounts = [];

						new_doc.is_modified = 1;
						new_doc.status = "Modified";
						new_doc.modification_version = frm.doc.modification_version + 1;
						new_doc.previous_lease = frm.doc.name;

						new_doc.parent_lease = frm.doc.parent_lease || frm.doc.name;

						frappe.set_route("Form", "Lease Management", new_doc.name);
					});
				}

				if (
					!frm.doc.parent_lease &&
					frm.doc.modifications &&
					frm.doc.modifications.length > 0
				) {
					frm.add_custom_button(
						__(`View Modifications (${frm.doc.modifications.length})`),
						function () {
							frm.scroll_to_field("modifications");
						}
					);
				}

				frm.add_custom_button(__("View Report"), function () {
					let lname = frm.doc.name;
					if (
						frm.doc.calculation_rate_type == "Daily Rate" &&
						frm.doc.lease_period == "Long Term (Greater Than 12 Months)"
					) {
						frappe.set_route("query-report", "Lease Report", {
							docname: lname,
						});
					} else if (
						frm.doc.calculation_rate_type == "Daily Rate" &&
						frm.doc.lease_period == "Short Term (Less Than 12 Months)"
					) {
						frappe.set_route("query-report", "Lease Report", {
							docname: lname,
						});
					} else if (
						frm.doc.calculation_rate_type == "Monthly Rate" &&
						frm.doc.lease_period == "Long Term (Greater Than 12 Months)"
					) {
						frappe.set_route(
							"query-report",
							"Lease Report Monthly (With Escalation)",
							{
								docname: lname,
							}
						);
					} else if (
						frm.doc.calculation_rate_type == "Monthly Rate" &&
						frm.doc.lease_period == "Short Term (Less Than 12 Months)"
					) {
						frappe.set_route(
							"query-report",
							"Lease Report Monthly (Without Escalation)",
							{
								docname: lname,
							}
						);
					}
				});
			}
			// if (frappe.user.has_role("Vendor") || frappe.user.has_role("Accounts")) {
			// 	frm.add_custom_button(__("Go to Invoice Details"), function () {
			// 		// Scroll to the field
			// 		frm.scroll_to_field("invoice_details");
			// 	});
			// }
		}
	},
	validate: function (frm) {
		// if(frm.doc.lease_period === "Long Term (Greater Than 12 Months)") {
		//     if(!frm.doc.escalation || frm.doc.escalation.length === 0) {
		//         frappe.msgprint(__('Escalation table is mandatory for Long Term leases.'));
		//         frappe.validated = false;  // prevent save
		//     }
		// }
		const invoice_rows = frm.doc.invoice_details || [];
		const attachments = frm.doc.invoice_attachments || [];
		let escalation = frm.doc.escalation || [];

		for (let i = 0; i < invoice_rows.length; i++) {
			const row = invoice_rows[i];

			// Match based on custom_row_id (mapped via your button logic)
			const matching_attachments = attachments.filter(
				(att) => att.invoice_row === row.custom_row_id
			);

			if (matching_attachments.length === 0) {
				frappe.throw(
					`Please add at least one attachment for the invoice row ${
						i + 1
					} (${frappe.datetime.str_to_user(
						row.from_date
					)} - ${frappe.datetime.str_to_user(row.to_date)}).`
				);
			}
		}
		// if (escalation.length === 0) return;

		let consecutivePerAnnum = 0;
		let consecutivePerAnnumandFixed = 0;

		escalation.forEach((row) => {
			if (row.escalation_type === "Per Annum") {
				consecutivePerAnnum += 1;
				consecutivePerAnnumandFixed = 0;
			} else if (row.escalation_type === "Per Annum and Fixed Amount") {
				consecutivePerAnnumandFixed += 1;
				consecutivePerAnnum = 0;
			} else {
				consecutivePerAnnum = 0;
				consecutivePerAnnumandFixed = 0;
			}

			if (consecutivePerAnnum >= 2) {
				frappe.throw(
					__(
						"You cannot have 2 or more consecutive 'Per Annum' values in escalation type"
					)
				);
			}

			if (consecutivePerAnnumandFixed >= 2) {
				frappe.throw(
					__(
						"You cannot have 2 or more consecutive 'Per Annum and Fixed Amount' values in escalation type"
					)
				);
			}

			// Validate mandatory fields for escalation types
			// if (row.escalation_type === "Based On Dates") {
			// 	if (!row.start_date || !row.end_date) {
			// 		frappe.msgprint(
			// 			`Start Date, End Date are mandatory for 'Based On Dates' escalation at row ${row.idx}`
			// 		);
			// 		frappe.validated = false;
			// 	} else if (!row.rate && !row.fixed_amount && !row.monthly_rent) {
			// 		frappe.msgprint(
			// 			`Set Monthly Rent / Rate / Fixed Amount for 'Based On Dates' escalation at row ${row.idx}`
			// 		);
			// 		frappe.validated = false;
			// 	}
			// }
		});

		if (
			frm.doc.property_description &&
			frm.doc.status != "Agreement Expired" &&
			!frm.doc.is_modified
		) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Lease Management",
					filters: {
						property_description: frm.doc.property_description,
						status: "Active",
					},
					fields: ["name", "agreement_start_date", "agreement_end_date"],
				},
				callback: function (response) {
					const leases = response.message || [];

					const today = frappe.datetime.get_today();

					const overlapping_lease = leases.find((lease) => {
						return (
							lease.agreement_start_date <= today &&
							lease.agreement_end_date >= today &&
							lease.name !== frm.doc.name // exclude current doc when editing
						);
					});

					if (overlapping_lease) {
						frappe.msgprint(
							`This property is already leased in agreement <b>${overlapping_lease.name}</b> from <b>${overlapping_lease.agreement_start_date}</b> to <b>${overlapping_lease.agreement_end_date}</b>.`
						);
						frappe.validated = false;
					}
				},
			});
		}
	},
});

function get_status_color(status) {
	const status_colors = {
		Active: "green",
		Terminated: "red",
		Modified: "blue",
		Discarded: "yellow",
		"Agreement Expired": "grey",
	};

	return status_colors[status] || "orange";
}

function set_lease_fields_readonly(frm) {
	let is_accounts = frappe.user.has_role("Accounts");
	let is_vendor = frappe.user.has_role("Vendor");
	let is_sys_manager = frappe.user.has_role("System Manager");

	// Apply restriction only if NOT System Manager
	if (
		(frm.doc.status === "Discarded" && (is_accounts || is_vendor) && !is_sys_manager) ||
		(frm.doc.status === "Terminated" && (is_accounts || is_vendor) && !is_sys_manager)
	) {
		// frm.fields.forEach(field => {
		//     if (field.df.fieldname) {
		//         frm.set_df_property(field.df.fieldname, "read_only", 1);
		//     }
		// });

		// Disable Save
		frm.disable_save();

		// Make all fields readonly
		frm.fields.forEach((field) => {
			if (field.df.fieldname) {
				frm.set_df_property(field.df.fieldname, "read_only", 1);
			}
		});

		// Disable child tables
		frm.fields.forEach((field) => {
			if (field.df.fieldtype === "Table") {
				let grid = frm.get_field(field.df.fieldname).grid;

				grid.wrapper.find(".grid-add-row").hide();
				grid.wrapper.find(".grid-remove-rows").hide();
				grid.wrapper.find(".grid-remove-all-rows").hide();
			}
		});
	}

	// frm.set_df_property("type_of_asset", "read_only", 1);
	// frm.set_df_property("company", "read_only", 1);
	// frm.set_df_property("vendor", "read_only", 1);
	// frm.set_df_property("property_description", "read_only", 1);
	// frm.set_df_property("discounting_rate", "read_only", 1);
	// frm.set_df_property("calculation_rate_type", "read_only", 1);
	// frm.set_df_property("previous_wdv", "read_only", 1);
	// frm.set_df_property("type_of_report", "read_only", 1);
	// frm.set_df_property("agreement_start_date", "read_only", 1);
	// frm.set_df_property("agreement_end_date", "read_only", 1);
	// frm.set_df_property("status", "read_only", 1);
	// frm.set_df_property("lease_period", "read_only", 1);
	// frm.set_df_property("security_deposit", "read_only", 1);
	// frm.set_df_property("security_deposit_amount", "read_only", 1);
	// frm.set_df_property("monthly_rent", "read_only", 1);
	// frm.set_df_property("agreement", "read_only", 1);
	// frm.set_df_property("modification_reason", "read_only", 1);
	// frm.set_df_property("termination_date", "read_only", 1);
	// frm.set_df_property("termination_reason", "read_only", 1);
	// frm.set_df_property("escalation", "read_only", 1);
	// frm.set_df_property("additional_amounts", "read_only", 1);
	// frm.set_df_property("modifications", "read_only", 1);
	// frm.set_df_property("invoice_details", "read_only", 1);
}

function set_agreement_status(frm) {
	const start_date = frm.doc.agreement_start_date;
	const end_date = frm.doc.agreement_end_date;
	if (start_date && end_date) {
		if (end_date <= start_date) {
			frappe.msgprint(__("Agreement End Date must be greater than Agreement Start Date."));
			frm.set_value("agreement_end_date", null);
			return;
		}

		let new_status = null;
		if (end_date < frappe.datetime.get_today()) {
			new_status = "Agreement Expired";
		} else {
			new_status = "Active";
		}
		if (frm.doc.status !== new_status) {
			frm.set_value("status", new_status);
			frm.save().then(() => {
				frm.reload_doc();
			});
		}
	}
}

function validate_dates_and_set_lease_period(frm) {
	if (!frm.doc.is_modified) {
		const start_date = frm.doc.agreement_start_date;
		const end_date = frm.doc.agreement_end_date;
		if (start_date && end_date) {
			if (end_date <= start_date) {
				frappe.msgprint(
					__("Agreement End Date must be greater than Agreement Start Date.")
				);
				frm.set_value("agreement_end_date", null);
				return;
			}

			// Calculate difference in months between dates
			const start = frappe.datetime.str_to_obj(start_date);
			const end = frappe.datetime.str_to_obj(end_date);

			let months_diff = (end.getFullYear() - start.getFullYear()) * 12;
			months_diff -= start.getMonth();
			months_diff += end.getMonth();

			if (months_diff > 12) {
				frm.set_value("lease_period", "Long Term (Greater Than 12 Months)");
			} else {
				frm.set_value("lease_period", "Short Term (Less Than 12 Months)");
			}

			if (end_date < frappe.datetime.get_today()) {
				frm.set_value("status", "Agreement Expired");
			} else {
				frm.set_value("status", "Active");
			}
		}
	}
}

function auto_set_start_end_date_escalation(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const agreement_start = frm.doc.agreement_start_date;
	const agreement_end = frm.doc.agreement_end_date;
	frappe.model.set_value(cdt, cdn, "start_date", agreement_start);
	frappe.model.set_value(cdt, cdn, "end_date", agreement_end);
	// if(row.escalation_type == 'Based On Dates'){
	//     //set start and end date to agreement start and end date
	//     frappe.model.set_value(cdt, cdn, 'start_date', agreement_start);
	//     frappe.model.set_value(cdt, cdn, 'end_date', agreement_end);
	// }
}

function update_custom_row_id(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	if (row.from_date && row.to_date) {
		let from_date = frappe.datetime.str_to_user(row.from_date); // dd-mm-yyyy
		let to_date = frappe.datetime.str_to_user(row.to_date);

		// Generate a temporary unique ID using timestamp or random if self.name is not available yet
		let parent_name = frm.doc.name || frm.doc.__unsaved || "TEMP";

		let idx = row.idx || 0;

		row.custom_row_id = `${parent_name}-row-${idx}-${from_date}-to-${to_date}`;
		frm.refresh_field("invoice_details");
	}
}

function validate_escalation_dates(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const agreement_start = frm.doc.agreement_start_date;
	const agreement_end = frm.doc.agreement_end_date;

	if (!agreement_start || !agreement_end) {
		frappe.msgprint(__("Please set Agreement Start Date and Agreement End Date first."));
		return;
	}

	if (row.start_date && row.end_date) {
		// Check escalation start/end dates are inside agreement range
		if (row.start_date < agreement_start || row.end_date > agreement_end) {
			frappe.msgprint(
				__(
					"Escalation Start and End Dates must be within Agreement Start and Agreement End Dates."
				)
			);
			frappe.model.set_value(cdt, cdn, "start_date", null);
			frappe.model.set_value(cdt, cdn, "end_date", null);
			return;
		}

		// Check escalation end date is greater than start date
		if (row.end_date <= row.start_date) {
			frappe.msgprint(__("Escalation End Date must be greater than Escalation Start Date."));
			frappe.model.set_value(cdt, cdn, "end_date", null);
		}
	}
}

function validate_additional_dates(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const agreement_start = frm.doc.agreement_start_date;
	const agreement_end = frm.doc.agreement_end_date;

	if (!agreement_start || !agreement_end) {
		frappe.msgprint(__("Please set Agreement Start Date and Agreement End Date first."));
		return;
	}

	if (row.start_date && row.end_date) {
		// Check start/end dates are inside agreement range
		if (row.start_date < agreement_start || row.end_date > agreement_end) {
			frappe.msgprint(
				__("Start and End Dates must be within Agreement Start and Agreement End Dates.")
			);
			frappe.model.set_value(cdt, cdn, "start_date", null);
			frappe.model.set_value(cdt, cdn, "end_date", null);
			return;
		}

		// Check end date is greater than start date
		if (row.end_date <= row.start_date) {
			frappe.msgprint(__("End Date must be greater than Start Date."));
			frappe.model.set_value(cdt, cdn, "end_date", null);
		}
	}
}

function validate_from_to_dates(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const agreement_start = frm.doc.agreement_start_date;
	const agreement_end = frm.doc.agreement_end_date;

	if (!agreement_start || !agreement_end) {
		frappe.msgprint(__("Please set Agreement Start Date and Agreement End Date first"));
		return;
	}

	if (row.from_date && row.to_date) {
		if (row.from_date < agreement_start || row.to_date > agreement_end) {
			frappe.msgprint(
				__(
					"Invoice From and To Dates must be within Agreement Start and Agreement End Dates"
				)
			);
			frappe.model.set_value(cdt, cdn, "from_date", null);
			frappe.model.set_value(cdt, cdn, "to_date", null);
			return;
		}

		if (row.to_date <= row.from_date) {
			frappe.msgprint(__("Invoice To Date must be greater than Invoice From Date"));
			frappe.model.set_value(cdt, cdn, "to_date", null);
		}
	}
}

function highlight_mismatched_rows(frm) {
	const grid = frm.fields_dict["invoice_details"].grid;
	grid.grid_rows.forEach((row) => {
		const row_data = row.doc;
		if (row.wrapper && row_data.is_mismatch == 1) {
			row.wrapper.css({
				// 'background-color':'#f59090ff'
				"background-color": "#f8d7da",
			});
		} else {
			row.wrapper.css({
				"background-color": "",
			});
		}
	});
}

function open_invoice_dialog() {
	let lease_id = null;
	let agreement_start = null;
	let agreement_end = null;

	let extra_attachments = [];

	const d = new frappe.ui.Dialog({
		title: "Add Invoice for Lease",
		fields: [
			{
				label: "Lease ID",
				fieldname: "lease_id",
				fieldtype: "Link",
				options: "Lease Management",
				reqd: 1,
				get_query: function () {
					return {
						filters: {
							status: "Active",
						},
					};
				},
				change: function () {
					lease_id = d.get_value("lease_id");
					if (lease_id) {
						load_lease_info(lease_id, d);
						toggle_invoice_fields(true);
					} else {
						toggle_invoice_fields(false);
					}
				},
			},
			{ fieldtype: "Section Break" },
			{
				label: "Agreement Start Date",
				fieldname: "start_date",
				fieldtype: "Date",
				read_only: 1,
			},
			{
				fieldtype: "Column Break",
			},
			{
				label: "Agreement End Date",
				fieldname: "end_date",
				fieldtype: "Date",
				read_only: 1,
			},
			{ fieldtype: "Section Break" },
			{
				label: "Previous Invoices",
				fieldname: "invoice_html",
				fieldtype: "HTML",
			},
			{ fieldtype: "Section Break" },
			{
				label: "Month",
				fieldname: "month",
				fieldtype: "Select",
				options:
					"January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
				reqd: 1,
			},
			{
				label: "From Date",
				fieldname: "from_date",
				fieldtype: "Date",
				reqd: 1,
			},
			{
				label: "To Date",
				fieldname: "to_date",
				fieldtype: "Date",
				reqd: 1,
			},
			{
				label: "Amount",
				fieldname: "amount",
				fieldtype: "Float",
				reqd: 1,
			},
			// {
			//     label: 'Invoice Attachment',
			//     fieldname: 'invoice_attachment',
			//     fieldtype: 'Attach',
			//     reqd: 1
			// },
			{
				label: "Attachments",
				fieldname: "manage_attachments",
				fieldtype: "Button",
			},
			{
				label: "With Tax",
				fieldname: "with_tax",
				fieldtype: "Check",
			},
			{
				label: "Tax (%)",
				fieldname: "tax",
				fieldtype: "Percent",
			},
		],
		primary_action_label: "Add Invoice",
		primary_action(values) {
			if (!lease_id) return;

			// ✅ Check if at least one attachment is added
			if (extra_attachments.length === 0) {
				frappe.msgprint(
					__("Please upload at least one attachment before adding invoice.")
				);
				return;
			}

			// ✅ Date validation
			const from_date = frappe.datetime.str_to_obj(values.from_date);
			const to_date = frappe.datetime.str_to_obj(values.to_date);
			const start_date = frappe.datetime.str_to_obj(agreement_start);
			const end_date = frappe.datetime.str_to_obj(agreement_end);

			if (from_date < start_date || to_date > end_date || from_date > to_date) {
				frappe.msgprint(
					__("From and To Dates must be within Agreement Start and End Date")
				);
				return;
			}

			// ✅ Proceed with invoice save
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Lease Management",
					name: lease_id,
				},
				callback: function (r) {
					if (r.message) {
						const doc = r.message;
						doc.invoice_details = doc.invoice_details || [];

						const current_length = (doc.invoice_details || []).length;
						const idx = current_length + 1;

						const formatDate = (dateStr) => {
							const d = frappe.datetime.str_to_obj(dateStr);
							return `${("0" + d.getDate()).slice(-2)}-${(
								"0" +
								(d.getMonth() + 1)
							).slice(-2)}-${d.getFullYear()}`;
						};

						const from_formatted = formatDate(values.from_date);
						const to_formatted = formatDate(values.to_date);

						const custom_row_id = `${lease_id}-row-${idx}-${from_formatted}-to-${to_formatted}`;

						const row = {
							month: values.month,
							from_date: values.from_date,
							to_date: values.to_date,
							amount: values.amount,
							with_tax: values.with_tax ? 1 : 0,
							tax: values.tax || 0,
							custom_row_id: custom_row_id,
						};

						doc.invoice_details.push(row);

						doc.invoice_attachments = doc.invoice_attachments || [];

						extra_attachments.forEach((file) => {
							const attachment_row = {
								file: file.file_url,
								file_docname: "", // Optionally set if available
								invoice_row: custom_row_id,
								uploaded_by: frappe.session.user,
								uploaded_on: frappe.datetime.now_datetime(),
							};

							if (!doc.invoice_attachments) {
								doc.invoice_attachments = [];
							}
							doc.invoice_attachments.push(attachment_row);
						});
						console.log("Extra attachments to save:", extra_attachments);

						frappe.call({
							method: "frappe.client.set_value",
							args: {
								doctype: "Lease Management",
								name: lease_id,
								fieldname: {
									invoice_details: doc.invoice_details,
									invoice_attachments: doc.invoice_attachments,
								},
							},
							callback: function (save_r) {
								if (!save_r.exc) {
									frappe.msgprint("Invoice added successfully.");
									d.hide();
								}
							},
						});
					}
				},
			});
		},
	});

	function toggle_invoice_fields(visible) {
		const fields_to_toggle = [
			"start_date",
			"end_date",
			"invoice_html",
			"month",
			"from_date",
			"to_date",
			"amount",
			"manage_attachments",
			"with_tax",
			"tax",
		];

		fields_to_toggle.forEach((fieldname) => {
			if (visible) {
				d.get_field(fieldname).$wrapper.show();
			} else {
				d.get_field(fieldname).$wrapper.hide();
			}
		});
	}

	d.show();
	toggle_invoice_fields(false);

	// Modified loader to store start/end dates in outer variables

	d.fields_dict.manage_attachments.input.onclick = () => {
		const upload_dialog = new frappe.ui.Dialog({
			title: "Upload Additional Attachments",
			fields: [],
		});

		upload_dialog.show();

		new frappe.ui.FileUploader({
			allow_multiple: 1,
			doctype: "Lease Management", // or your doctype
			docname: lease_id, // the current document name
			folder: "Home/Attachments", // optional folder
			on_success: (file) => {
				extra_attachments.push({
					file_url: file.file_url,
					name: frappe.utils.get_random(10),
				});
				frappe.msgprint("Attachment added: " + file.file_name);
				upload_dialog.hide();
			},
			onerror: (err) => {
				frappe.msgprint(__("Upload failed: {0}", [err]));
			},
		});
	};

	function load_lease_info(lease_id, dialog) {
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Lease Management",
				name: lease_id,
			},
			callback: function (r) {
				const doc = r.message;
				agreement_start = doc.agreement_start_date;
				agreement_end = doc.agreement_end_date;

				dialog.set_value("start_date", agreement_start);
				dialog.set_value("end_date", agreement_end);

				let html = `
                <div style="margin-bottom: 10px;">
                    <strong style="font-size: 14px;">Previous Invoices</strong>
                </div>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th>From</th>
                            <th>To</th>
                            <th>Amount</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>`;

				const invoices = doc.invoice_details || [];

				if (invoices.length === 0) {
					html += `<tr>
                        <td colspan="5" class="text-center text-muted">No Invoice Details Added Yet.</td>
                    </tr>`;
				} else {
					invoices.forEach((inv) => {
						html += `<tr>
                            <td>${inv.month}</td>
                            <td>${inv.from_date}</td>
                            <td>${inv.to_date}</td>
                            <td>${inv.amount}</td>
                            <td>${inv.payment_status || "Unpaid"}</td>
                        </tr>`;
					});
				}

				html += "</tbody></table>";

				dialog.fields_dict.invoice_html.$wrapper.html(html);
			},
		});
	}
}
