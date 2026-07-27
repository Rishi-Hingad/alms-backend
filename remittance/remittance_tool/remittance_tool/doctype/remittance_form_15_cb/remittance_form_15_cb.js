// Sum child table (Remittance Invoice) values into parent totals.
// Mapping:
//   amount_payable_foreign = SUM of qsshb    (Withhldg tax base amount)
//   amount_payable_inr     = SUM of zzqsshb  (Withhldg tax base amount INR)
//   base_amount_foreign    = SUM of wrshb    (Amount in doc. curr.)
//   base_amount_inr        = SUM of dmshb    (Amount in local currency)
function calculate_invoice_totals(frm) {
	let amount_payable_foreign = 0,
		amount_payable_inr = 0,
		net_amount_foreign = 0,
		net_amount_inr = 0;

	(frm.doc.invoices || []).forEach((row) => {
		amount_payable_foreign += row.qsshb || 0;
		amount_payable_inr += row.zzqsshb || 0;
		net_amount_foreign += row.wrshb || 0;
		net_amount_inr += row.dmshb || 0;
	});

	frm.set_value("amount_payable_foreign", amount_payable_foreign);
	frm.set_value("amount_payable_inr", Math.round(amount_payable_inr));
	frm.set_value("net_amount_foreign", net_amount_foreign);
	frm.set_value("net_amount_inr", Math.round(net_amount_inr));
}

frappe.ui.form.on("Remittance Invoice", {
	qsshb: calculate_invoice_totals,
	zzqsshb: calculate_invoice_totals,
	wrshb: calculate_invoice_totals,
	dmshb: calculate_invoice_totals,
	invoices_remove: calculate_invoice_totals,
	// form_render: function(frm, cdt, cdn) {
    //     const isAdmin = frappe.session.user === 'Administrator';

    //     if (!isAdmin) {
    //         // target the open row form
    //         $('.grid-row-open .grid-delete-row').hide();
    //     }
    // }
});

frappe.ui.form.on("Remittance Form 15 CB", {
	onload: function (frm) {
		// store original formatter
        let original = frappe.form.formatters.Currency;

        frappe.form.formatters.Currency = function(value, df, options, doc) {

            // remove ₹ + format as float
            return (value || 0).toFixed(2);
        };
		if (frm.doc.dtaa_name) {
			set_dtaa_articles(frm);
		}
		if (frm.doc.status === "Approved") {
			set_fields_readonly(frm);
		}
	},
	on_unload(frm) {
        // optional: restore if needed
        frappe.form.formatters.Currency = null;
    },
	refresh: function (frm) {
		let grid = frm.get_field('invoices').grid;
        const isAdmin = frappe.session.user === 'Administrator';

        // grid.cannot_add_rows = !isAdmin;
        // grid.cannot_delete_rows = !isAdmin;

        // hide delete buttons in rows
        if (!isAdmin) {
			frm.set_df_property("invoices", "read_only", 1);
            // grid.wrapper.find('.grid-remove-rows').hide();
            // grid.wrapper.find('.grid-remove-row').hide();
        }

        frm.refresh_field('invoices');

		frm.meta.fields.forEach(df => {

            if (df.fieldtype === "Currency") {

                let fieldname = df.fieldname;
                let value = frm.doc[fieldname];

                if (value != null && frm.fields_dict[fieldname]) {

                    let formatted = (value || 0).toFixed(2); // float, no commas

                    frm.fields_dict[fieldname].$wrapper
                        .find('.control-value')
                        .html(`<div style="text-align: left">${formatted}</div>`);
                }
            }

        });

		if (
			(frm.doc.status === "Pending Approval" && frm.doc.approval_entry) ||
			(frm.doc.status === "Sent Back" && frm.doc.approval_entry)
		) {
			frappe.db.get_doc("Approval Entry", frm.doc.approval_entry).then((approval_doc) => {
				let child_table = approval_doc.approval_entry;
				if (!child_table || !child_table.length) return;

				let recent_row = child_table[child_table.length - 1];
				let expected_approver = recent_row.next_approver;     // user-stage
				let expected_role = recent_row.next_approver_role;     // role-stage
				let current_user = frappe.session.user;

				// User can approve if:
				//   - they ARE the named next_approver (user stage)
				//   - they have the required role (role stage)
				//   - they are Administrator
				let is_named_user = expected_approver && current_user === expected_approver;
				let has_required_role = expected_role && frappe.user.has_role(expected_role);
				let is_admin = current_user === "Administrator";

				if (!is_named_user && !has_required_role && !is_admin) {
					frm.disable_form(); // Lock the form for non-approvers

					// Headline: prefer the actual user; otherwise show role name
					let waiting_msg;
					if (expected_approver) {
						waiting_msg = `Waiting for approval from: ${expected_approver}`;
					} else if (expected_role) {
						waiting_msg = `Waiting for approval from role: ${expected_role}`;
					} else {
						waiting_msg = "Waiting for approval";
					}
					frm.dashboard.set_headline(waiting_msg);
				}
			});
		}

		if (frm.doc.status === "Rejected" && !frappe.user.has_role("Remittance User")) {
			frm.disable_form();
		}

		if (frm.doc.dtaa_name) {
			set_dtaa_articles(frm);
		}
		if (!frm.is_new()) {
			// Role gate for the audit/trail buttons. Change this single string
			// to switch which role can see them.
			const TRAIL_ROLE = "Approval Auditor";
			const can_view_trail =
				frappe.session.user === "Administrator" || frappe.user.has_role(TRAIL_ROLE);

			// Only show approval-history buttons once the flow has actually started
			const flow_started = !!(
				frm.doc.approval_initiated ||
				frm.doc.approval_entry ||
				frm.doc.is_submitted
			);

			if (can_view_trail && flow_started) {
				// View Approval Trail — restricted to "Approval Auditor"
				frm.add_custom_button(__("View Approval Trail"), function () {
					show_approval_trail(frm);
				});

				// Approval Details — compact card-style summary
				frm.add_custom_button(__("Approval Details"), function () {
					show_approval_details(frm);
				});
			}

			// Send / Resubmit for Approval — only the Maker (doc owner) can submit
			const is_maker =
				frm.doc.owner === frappe.session.user || frappe.session.user === "Administrator";

			if (!frm.doc.is_submitted && is_maker && frappe.user.has_role("Remittance User")) {
				const needs_resubmit =
					frm.doc.status === "Rejected" || frm.doc.status === "Sent Back";
				const btn_label = needs_resubmit
					? __("Resubmit for Approval")
					: __("Send for Approval");
				const confirm_msg = needs_resubmit
					? __("Resubmit this Form 15CB — approval will restart from the beginning.")
					: __("Submit this Form 15CB into the approval matrix?");

				frm.add_custom_button(btn_label, function () {
					frappe.confirm(confirm_msg, function () {
						frappe.call({
							method: "remittance_tool.remittance_tool.api.approval.submit_for_approval",
							args: { doctype: frm.doctype, doc_name: frm.doc.name },
							freeze: true,
							freeze_message: __("Submitting for approval..."),
							callback: function (r) {
								if (r.message && r.message.status === "success") {
									frappe.show_alert({
										message: needs_resubmit
											? __("Resubmitted for approval")
											: __("Sent for approval"),
										indicator: "green",
									});
									frm.reload_doc();
								} else if (r.message) {
									frappe.msgprint(r.message.message || "");
									frm.reload_doc();
								}
							},
						});
					});
				}).addClass("btn-primary");
			}

			// Approve / Reject / Send Back — only for the user whose turn it is right now
			frappe.call({
				method: "remittance_tool.remittance_tool.api.approval.get_approval_status",
				args: { doc_type: frm.doctype, doc_name: frm.docname },
				callback: function (r) {
					if (r.message && r.message.is_approver) {
						frm.add_custom_button(__("Approve"), function () {
							approve_reject_dialog(frm, "Approve");
						}).addClass("btn-primary");

						frm.add_custom_button(__("Send Back"), function () {
							approve_reject_dialog(frm, "SendBack");
						});

						frm.add_custom_button(__("Reject"), function () {
							approve_reject_dialog(frm, "Reject");
						}).addClass("btn-danger");
					}
				},
			});
			// 📎 Send Documents + View JSON: only the form owner (or Administrator) can see them.
			const is_form_owner = frm.doc.owner === frappe.session.user || frappe.session.user === "Administrator";
			if (frm.doc.status === "Approved" && is_form_owner) {
				// frm.add_custom_button("View XML", function () {
				// 	frappe.call({
				// 		method: "remittance_tool.remittance_tool.api.xml_generator.generate_remittance_xml",
				// 		args: {
				// 			docname: frm.doc.name,
				// 		},
				// 		callback: function (r) {
				// 			if (r.message) {
				// 				let dialog = new frappe.ui.Dialog({
				// 					title: "XML Viewer",
				// 					size: "extra-large",
				// 					fields: [
				// 						{
				// 							fieldtype: "HTML",
				// 							fieldname: "xml_content",
				// 						},
				// 					],
				// 				});

				// 				dialog.show();

				// 				dialog.fields_dict.xml_content.$wrapper.html(
				// 					`<pre style="max-height:600px; overflow:auto; background:#1e1e1e; padding:15px;color:white;">
				// 						${frappe.utils.escape_html(r.message)}
				// 					</pre>
				// 					<br>
				// 					<button class="btn btn-primary" id="download_xml">
				// 						Download XML
				// 					</button>`
				// 				);

				// 				dialog.$wrapper.find("#download_xml").on("click", function () {
				// 					let blob = new Blob([r.message], { type: "application/xml" });
				// 					let url = URL.createObjectURL(blob);

				// 					let a = document.createElement("a");
				// 					a.href = url;
				// 					a.download = frm.doc.name + ".xml";
				// 					a.click();
				// 				});
				// 			}
				// 		},
				// 	});
				// });

			

				frm.add_custom_button("📎 Send Documents", function () {
					open_send_attachments_dialog(frm);
				}).addClass("btn-success");

				frm.add_custom_button("View JSON", function () {
					frappe.call({
						method: "remittance_tool.remittance_tool.api.json_generator.generate_remittance_json",
						args: {
							docname: frm.doc.name,
						},
						freeze: true,
						freeze_message: __("Building JSON..."),
						callback: function (r) {
							if (!r.message) return;

							// Pretty-print JSON if valid
							let formatted_json = r.message;
							try {
								formatted_json = JSON.stringify(JSON.parse(r.message), null, 4);
							} catch (e) {
								// If response isn't valid JSON, display as-is
							}

							let dialog = new frappe.ui.Dialog({
								title: "JSON Viewer",
								size: "extra-large",
								fields: [
									{
										fieldtype: "HTML",
										fieldname: "json_content",
									},
								],
							});

							dialog.show();

							dialog.fields_dict.json_content.$wrapper.html(`
								<div style="margin-bottom:15px;">
									<button class="btn btn-default" id="toggle_theme">
										🌙 Dark Mode
									</button>

									<button class="btn btn-primary" id="download_json" style="margin-left:8px;">
										Download JSON
									</button>

									<button class="btn btn-success" id="send_json_to_ca" style="margin-left:8px;">
										✉ Send to CA
									</button>

									<button class="btn btn-default" id="copy_json" style="margin-left:8px;">
										Copy to Clipboard
									</button>
								</div>

								<div
									id="json_container"
									style="
										background:#ffffff;
										border:1px solid #d1d5db;
										border-radius:8px;
										padding:16px;
										max-height:600px;
										overflow:auto;
										transition: all 0.25s ease;
									"
								>
									<pre
										id="json_pre"
										style="
											margin:0;
											background:transparent;
											color:#1f2937;
											font-family:Consolas, Monaco, 'Courier New', monospace;
											font-size:14px;
											line-height:1.6;
											white-space:pre-wrap;
											word-break:break-word;
										"
									>${frappe.utils.escape_html(formatted_json)}</pre>
								</div>
							`);

							let darkMode = false;

							dialog.$wrapper.find("#toggle_theme").on("click", function () {
								darkMode = !darkMode;

								const container = dialog.$wrapper.find("#json_container");
								const pre = dialog.$wrapper.find("#json_pre");
								const button = $(this);

								if (darkMode) {
									container.css({
										background: "#1e1e1e",
										border: "1px solid #3c3c3c"
									});

									pre.css({
										color: "#d4d4d4"
									});

									button.text("☀️ Light Mode");
								} else {
									container.css({
										background: "#ffffff",
										border: "1px solid #d1d5db"
									});

									pre.css({
										color: "#1f2937"
									});

									button.text("🌙 Dark Mode");
								}
							});

							dialog.$wrapper.find("#download_json").on("click", function () {
								let blob = new Blob([formatted_json], {
									type: "application/json",
								});

								let url = URL.createObjectURL(blob);

								let a = document.createElement("a");
								a.href = url;
								a.download = frm.doc.name + ".json";
								a.click();

								URL.revokeObjectURL(url);
							});

							dialog.$wrapper.find("#copy_json").on("click", function () {
								copy_text_to_clipboard(formatted_json);
							});

							dialog.$wrapper.find("#send_json_to_ca").on("click", function () {
								open_send_json_to_ca_dialog(frm);
							});
						},
					});
				});
			}
		}

		setTimeout(() => {
			if (!frm.fields_dict.section_of_act?.$input) return;

			frm.fields_dict.section_of_act.$input.off("focus");

			frm.fields_dict.section_of_act.$input.on("focus", function () {
				if (!frm.doc.nature_of_remittance) {
					frappe.msgprint("Please select Nature of Remittance first");
					return;
				}

				frappe.call({
					method: "frappe.client.get",
					args: {
						doctype: "Remittance Nature",
						name: frm.doc.nature_of_remittance,
					},
					callback: function (r) {
						// Filter only enabled rows
						let sections = (r.message.section_of_act || []).filter(
							(row) => row.enabled
						);

						if (!sections.length) {
							frappe.msgprint("No Sections found for selected Nature");
							return;
						}

						// If only one record → auto set & skip dialog
						if (sections.length === 1) {
							frm.set_value("section_of_act", sections[0].description);
							return;
						}

						let d = new frappe.ui.Dialog({
							title: "Select Section of Act",
							size: "large",
							fields: [
								{
									fieldtype: "Table",
									fieldname: "sections_table",
									label: "Available Sections",
									cannot_add_rows: true,
									cannot_delete_rows: true,
									in_place_edit: false,
									reqd: 1,
									data: sections.map((row) => ({
										description: row.description,
									})),
									fields: [
										{
											fieldtype: "Data",
											fieldname: "description",
											label: "Section Description",
											in_list_view: 1,
											read_only: 1,
											cannot_edit: true,
										},
									],
								},
							],
							primary_action_label: "Select",
							primary_action() {
								let grid = d.fields_dict.sections_table.grid;
								let selected = grid.get_selected_children();

								if (selected.length !== 1) {
									frappe.msgprint("Please select one row");
									return;
								}

								frm.set_value("section_of_act", selected[0].description);
								d.hide();
							},
						});

						d.show();

						let grid = d.fields_dict.sections_table.grid;

						// Hide add/remove buttons
						grid.wrapper.find(".grid-remove-rows").hide();
						grid.wrapper.find(".grid-add-row").hide();

						grid.wrapper.find(".grid-heading-row .grid-row-check").hide();
						grid.wrapper.find(".grid-row-open").hide();
						grid.wrapper.find(".grid-delete-row").remove();

						// Force single checkbox selection
						grid.wrapper.on("click", ".grid-row-check", function () {
							let checked_row = $(this).closest(".grid-row");

							grid.wrapper.find(".grid-row-check").not(this).prop("checked", false);
							grid.grid_rows.forEach((row) => row.select(false));

							let docname = checked_row.attr("data-name");
							let row = grid.grid_rows_by_docname[docname];
							if (row) row.select(true);
						});

						// Preselect previously saved value
						let current_value = (frm.doc.section_of_act || "").trim();

						setTimeout(() => {
							grid.grid_rows.forEach((row) => {
								let row_value = (row.doc.description || "").trim();

								if (row_value === current_value) {
									row.select(true);
									$(row.row).find(".grid-row-check").prop("checked", true);
								}
							});
						}, 200);
					},
				});
			});
		}, 300);

		if (frm.fields_dict.basis_for_taxable_income_and_tax_liability_calculation?.$input) {
			frm.fields_dict.basis_for_taxable_income_and_tax_liability_calculation.$input.off(
				"focus"
			);

			frm.fields_dict.basis_for_taxable_income_and_tax_liability_calculation.$input.on(
				"focus",
				function () {
					if (!frm.doc.nature_of_remittance) {
						frappe.msgprint("Please select Nature of Remittance first");
						return;
					}

					frappe.call({
						method: "frappe.client.get",
						args: {
							doctype: "Remittance Nature",
							name: frm.doc.nature_of_remittance,
						},
						callback: function (r) {
							let basis_records = (r.message.basis_of_determining || []).filter(
								(row) => row.enabled
							);
							if (!basis_records.length) {
								frappe.msgprint(
									"No Basis of Determination found for selected Nature"
								);
								return;
							}

							// If only one record → auto set & skip dialog
							if (basis_records.length === 1) {
								frm.set_value(
									"basis_for_taxable_income_and_tax_liability_calculation",
									basis_records[0]
										.basis_of_determining_taxable_income_and_tax_liability +
									" - {Tax Rate = " +
									basis_records[0].tax +
									"%}"
								);
								frm.set_value("tds_rate_income_tax_act", basis_records[0].tax);
								return;
							}

							let d = new frappe.ui.Dialog({
								title: "Select Basis of Determination",
								size: "large",
								fields: [
									{
										fieldtype: "Table",
										fieldname: "basis_table",
										label: "Available Records",
										cannot_add_rows: true,
										cannot_delete_rows: true,
										in_place_edit: false,
										reqd: 1,
										data: basis_records.map((row) => ({
											description:
												row.basis_of_determining_taxable_income_and_tax_liability,
											tax: row.tax,
										})),
										fields: [
											{
												fieldtype: "Data",
												fieldname: "description",
												label: "Basis Description",
												in_list_view: 1,
												read_only: 1,
												cannot_edit: 1,
											},
											{
												fieldtype: "Percent",
												fieldname: "tax",
												label: "Tax",
												in_list_view: 1,
												read_only: 1,
												cannot_edit: 1,
											},
										],
									},
								],
								primary_action_label: "Select",
								primary_action() {
									let grid = d.fields_dict.basis_table.grid;
									let selected = grid.get_selected_children();

									if (selected.length !== 1) {
										frappe.msgprint("Please select one row");
										return;
									}

									frm.set_value(
										"basis_for_taxable_income_and_tax_liability_calculation",
										selected[0].description +
										" - {Tax Rate = " +
										selected[0].tax +
										"%}"
									);
									frm.set_value("tds_rate_income_tax_act", selected[0].tax);

									d.hide();
								},
							});

							d.show();

							let grid = d.fields_dict.basis_table.grid;
							// Hide add/remove buttons
							grid.wrapper.find(".grid-remove-rows").hide();
							grid.wrapper.find(".grid-add-row").hide();

							grid.wrapper.find(".grid-heading-row .grid-row-check").hide();
							grid.wrapper.find(".grid-row-open").hide();
							grid.wrapper.find(".grid-delete-row").remove();

							// Force single checkbox selection
							grid.wrapper.on("click", ".grid-row-check", function () {
								let checked_row = $(this).closest(".grid-row");

								grid.wrapper
									.find(".grid-row-check")
									.not(this)
									.prop("checked", false);
								grid.grid_rows.forEach((row) => row.select(false));

								let docname = checked_row.attr("data-name");
								let row = grid.grid_rows_by_docname[docname];
								if (row) row.select(true);
							});

							// Preselect previously saved value
							let current_value = (
								frm.doc.basis_for_taxable_income_and_tax_liability_calculation ||
								""
							).trim();

							setTimeout(() => {
								grid.grid_rows.forEach((row) => {
									let row_value = (row.doc.description || "").trim();

									if (row_value === current_value.split("-")[0].trim()) {
										row.select(true);
										$(row.row).find(".grid-row-check").prop("checked", true);
									}
								});
							}, 200);
						},
					});
				}
			);
		}

		if (frm.fields_dict.basis_for_tax_deduction_rate?.$input) {
			frm.fields_dict.basis_for_tax_deduction_rate.$input.off("focus");

			frm.fields_dict.basis_for_tax_deduction_rate.$input.on(
				"focus",
				function () {

					frappe.call({
						method: "frappe.client.get_list",
						args: {
							doctype: "Basis of Arriving",
							filters: {
								is_enabled: 1
							},
							fields: ["name"],
							limit_page_length: 1
						},
						callback: function (res) {

							if (!res.message || !res.message.length) {
								frappe.msgprint("No enabled Basis of Arriving found");
								return;
							}

							let basis_name = res.message[0].name;

							frappe.call({
								method: "frappe.client.get",
								args: {
									doctype: "Basis of Arriving",
									name: basis_name
								},
								callback: function (r) {

									let doc = r.message;

									// let option1 = (doc.option_1 || [])
									// 	.filter(row => row.enabled)
									// 	.map(row => ({
									// 		basis: row.basis,
									// 		type: "Option 1",
									// 		from_date: "",
									// 		to_date: ""
									// 	}));
									let option1 = (doc.option_1 || [])
										.filter(row => row.enabled)
										.map(row => ({

											basis: (row.basis || "").replace(
												/{nature_of_remittance}/g,
												frm.doc.nature_of_remittance || "<nature of remittance>"
											)
											.replace(
												/{article}/g,
												frm.doc.article || "<article>"
											)
											.replace(
												/{dtaa_name}/g,
												frm.doc.dtaa_name || "<dtaa_name>"
											),

											type: "Option 1"
										}));


									// let option2 = (doc.option_2 || [])
									// 	.filter(row => row.enabled)
									// 	.map(row => ({
									// 		basis: row.basis,
									// 		type: "Option 2",
									// 		from_date: row.from_date || "",
									// 		to_date: row.to_date || ""
									// 	}));
									let option2 = (doc.option_2 || [])
										.filter(row => row.enabled)
										.map(row => ({
											basis: row.basis,
											type: "Option 2"
										}));

									let all_records = [...option1, ...option2];

									if (!all_records.length) {
										frappe.msgprint("No enabled records found");
										return;
									}

									// Auto set if only one
									if (all_records.length === 1) {

										frm.set_value(
											"basis_for_tax_deduction_rate",
											all_records[0].basis
										);

										return;
									}

									let d = new frappe.ui.Dialog({
										title: "Select Basis For Tax Deduction Rate",
										size: "large",
										fields: [
											{
												fieldtype: "Table",
												fieldname: "basis_table",
												label: "Available Records",
												cannot_add_rows: true,
												cannot_delete_rows: true,
												in_place_edit: false,
												reqd: 1,
												data: all_records,
												fields: [
													{
														fieldtype: "Data",
														fieldname: "type",
														label: "Type",
														in_list_view: 1,
														read_only: 1
													},
													{
														fieldtype: "Data",
														fieldname: "basis",
														label: "Basis",
														in_list_view: 1,
														read_only: 1
													}
													
													// {
													// 	fieldtype: "Date",
													// 	fieldname: "from_date",
													// 	label: "From Date",
													// 	in_list_view: 1,
													// 	read_only: 1
													// },
													// {
													// 	fieldtype: "Date",
													// 	fieldname: "to_date",
													// 	label: "To Date",
													// 	in_list_view: 1,
													// 	read_only: 1
													// }
												]
											}
										],

										primary_action_label: "Select",

										primary_action() {

											let grid = d.fields_dict.basis_table.grid;
											let selected = grid.get_selected_children();

											if (selected.length !== 1) {
												frappe.msgprint("Please select one row");
												return;
											}

											frm.set_value(
												"basis_for_tax_deduction_rate",
												selected[0].basis
											);

											d.hide();
										}
									});

									d.show();

									let grid = d.fields_dict.basis_table.grid;

									// Hide buttons
									grid.wrapper.find(".grid-remove-rows").hide();
									grid.wrapper.find(".grid-add-row").hide();
									grid.wrapper.find(".grid-heading-row .grid-row-check").hide();
									grid.wrapper.find(".grid-row-open").hide();
									grid.wrapper.find(".grid-delete-row").remove();

									// Single select only
									grid.wrapper.on("click", ".grid-row-check", function () {

										let checked_row = $(this).closest(".grid-row");

										grid.wrapper
											.find(".grid-row-check")
											.not(this)
											.prop("checked", false);

										grid.grid_rows.forEach((row) => row.select(false));

										let docname = checked_row.attr("data-name");
										let row = grid.grid_rows_by_docname[docname];

										if (row) {
											row.select(true);
										}
									});

									// Preselect current value
									let current_value = (
										frm.doc.basis_for_tax_deduction_rate || ""
									).trim();

									setTimeout(() => {

										grid.grid_rows.forEach((row) => {

											let row_value = (row.doc.basis || "").trim();

											if (row_value === current_value) {

												row.select(true);

												$(row.row)
													.find(".grid-row-check")
													.prop("checked", true);
											}
										});

									}, 200);
								}
							});
						}
					});
				}
			);
		}
	},
	nature_of_remittance: function (frm) {
		if (!frm.doc.nature_of_remittance) return;

		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Remittance Nature",
				name: frm.doc.nature_of_remittance,
			},
			callback: function (r) {
				if (!r.message) return;

				let data = r.message;

				// -------------------------------
				// SECTION OF ACT
				// -------------------------------
				let sections = (data.section_of_act || []).filter((row) => row.enabled);

				if (sections.length === 1) {
					frm.set_value("section_of_act", sections[0].description);
				} else {
					// Optional: clear if multiple
					frm.set_value("section_of_act", "");
				}

				// -------------------------------
				// BASIS OF DETERMINATION
				// -------------------------------
				let basis_records = (data.basis_of_determining || []).filter((row) => row.enabled);

				if (basis_records.length === 1) {
					frm.set_value(
						"basis_for_taxable_income_and_tax_liability_calculation",
						basis_records[0].basis_of_determining_taxable_income_and_tax_liability +
						" - {Tax Rate = " +
						basis_records[0].tax +
						"%}"
					);

					frm.set_value("tds_rate_income_tax_act", basis_records[0].tax);
				} else {
					// Optional: clear if multiple
					frm.set_value("basis_for_taxable_income_and_tax_liability_calculation", "");
					frm.set_value("tds_rate_income_tax_act", "");
				}
			},
		});
	},
	vendor: function (frm) {
		if (frm.doc.vendor) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Remittance Vendor",
					name: frm.doc.vendor,
				},
				callback: function (r) {
					if (r.message) {
						let v = r.message;

						let address_parts = [
							v.address_line_1,
							v.address_line_2,
							v.road_street,
							v.area_locality,
							v.city_district,
							v.state,
							v.country,
							v.zip_code,
						];

						// Remove empty/null values
						address_parts = address_parts.filter(Boolean);

						// Join with comma
						let full_address = address_parts.join(", ");

						frm.set_value("vendor_address", full_address);
					}
				},
			});
		}
	},
	dtaa_name: function (frm) {
		if (frm.doc.dtaa_name) {
			set_dtaa_articles(frm);
		} else {
			frm.set_df_property("dtaa_article", "options", "");
			frm.set_value("dtaa_article", "");
		}
	},
	dtaa_article: function (frm) {
		if (frm.doc.dtaa_article) {
			let dtaa_article = frm.doc.dtaa_article;
			let a = dtaa_article.split("-");
			let art_desc = a.at(-1);

			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "DTAA Master",
					name: frm.doc.dtaa_name,
				},
				callback: function (r) {
					let dtaa_doc = r.message;
					dtaa_doc.articles.forEach(function (row) {
						if (row.enabled && row.article_description.trim() === art_desc.trim()) {
							frm.set_value("tds_rate_as_per_dtaa", row.tax);
							frm.set_value("tds_rate_dtaa", row.tax);
							frm.set_value("article", row.article_no);
						}
					});
				},
			});
		}
		trigger_calc(frm);
	},
	tax_category: function (frm) {
		if (frm.doc.tax_category == "Royalty / FTS / Interest / Dividend") {
			if (frm.doc.dtaa_article) {
				let dtaa_article = frm.doc.dtaa_article;
				frm.set_value("applicable_dtaa_article", dtaa_article);
			}
		}
		else {
			frm.set_value("applicable_dtaa_article", "");
		}
		if (frm.doc.tax_category != "Business Income"){
			frm.set_value("income_taxable_in_india","");
			frm.set_value("basis_for_tax_deduction_rate","");
		}
		if (frm.doc.tax_category != "Capital Gains"){
			frm.set_value("long_term_capital_gains_amount",0);
			frm.set_value("short_term_capital_gains_amount",0);
			frm.set_value("basis_for_taxable_income_calculation","");
		}
		if (frm.doc.tax_category != "Other"){
			frm.set_value("specify_nature_of_remittance","");
			frm.set_value("taxable_in_india_as_per_dtaa",0);
			frm.set_value("applicable_tds_rate",0);
			frm.set_value("reason_for_non_taxability","");
		}
		// if (frm.doc.tax_category == "Other"){
		// 	frappe.msgprint("taxable_in_india_as_per_dtaa="+structuredClone(frm.doc.taxable_in_india_as_per_dtaa));
		// 	if (!frm.doc.taxable_in_india_as_per_dtaa){
		// 		frm.set_value("applicable_tds_rate",0);
		// 	}
		// 	else{
		// 		frm.set_value("reason_for_non_taxability","");
		// 	}
		// }
	},
	taxable_in_india_as_per_dtaa:function(frm){	
		if (!frm.doc.taxable_in_india_as_per_dtaa){
			frm.set_value("applicable_tds_rate",0);
		}
		else{
			frm.set_value("reason_for_non_taxability","");
		}
	},
	exchange_rate: trigger_calc,
	tds_rate_income_tax_act: trigger_calc,
	tds_rate_as_per_dtaa: trigger_calc,
	trc_obtained: function (frm){
		trigger_calc(frm);
		if (!frm.doc.trc_obtained) {
            const fields_to_clear = [
                "dtaa_name",
                "dtaa_article",
                "dtaa_taxable_income",
                "dtaa_tax_liability",
                "tax_category",
                "applicable_dtaa_article",
                "tds_rate_as_per_dtaa",
                "income_taxable_in_india",
                "basis_for_tax_deduction_rate",
                "long_term_capital_gains_amount",
                "short_term_capital_gains_amount",
                "basis_for_taxable_income_calculation",
                "specify_nature_of_remittance",
                "taxable_in_india_as_per_dtaa",
                "applicable_tds_rate",
                "reason_for_non_taxability",
				"tds_rate_dtaa",
				"tax_residency_number"
            ];

            // Clear values
            fields_to_clear.forEach(field => {
                frm.set_value(field, null);
            });
        }
	},
	gross_up: trigger_calc,
	net_amount_inr: function (frm) {
		if (frm.__updating_amounts) return;

		if (frm.doc.net_amount_inr != null && frm.doc.exchange_rate) {
			frm.__updating_amounts = true;
			frm.__last_changed = "inr";

			frm.set_value("net_amount_foreign", frm.doc.net_amount_inr / frm.doc.exchange_rate);

			frm.__updating_amounts = false;
		}

		// IMPORTANT: call AFTER value sync
		trigger_calc(frm);
	},
	net_amount_foreign: function (frm) {
		if (frm.__updating_amounts) return;

		if (frm.doc.net_amount_foreign != null && frm.doc.exchange_rate) {
			frm.__updating_amounts = true;
			frm.__last_changed = "foreign";

			frm.set_value("net_amount_inr", frm.doc.net_amount_foreign * frm.doc.exchange_rate);

			frm.__updating_amounts = false;
		}

		trigger_calc(frm);
	},
	before_vat_amount:function(frm){
		calculate_vat_totals(frm);
	},
	vat:function(frm){
		calculate_vat_totals(frm);
	},
});

function format_child_currency(grid, fieldname) {

    grid.grid_rows.forEach(row => {

        let value = row.doc[fieldname];

        let cell = $(row.columns?.[fieldname]?.field_area);

        if (cell.length && value != null) {

            let formatted = (value || 0).toFixed(2);
			console.log("Checking formateed value : " + formatted + " of type " + typeof formatted);

            cell.find('.control-value')
                .text(formatted);
        }
    });

}

function calculate_vat_totals(frm) {
	// if (frm.doc.before_vat_amount && frm.doc.vat){
	total= parseFloat(frm.doc.before_vat_amount) + parseFloat(frm.doc.vat);
	frm.set_value("total_amount", total);
	// }
}

function set_dtaa_articles(frm) {
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "DTAA Master",
			name: frm.doc.dtaa_name,
		},
		callback: function (r) {
			if (!r.message) return;

			let options = [];

			(r.message.articles || []).forEach(function (row) {
				if (row.enabled) {
					options.push(row.article_no + " - " + row.article_description);
				}
			});

			frm.set_df_property("dtaa_article", "options", options.join("\n"));

			frm.refresh_field("dtaa_article");
		},
	});
}

function trigger_calc(frm) {
	frappe.call({
		method: "remittance_tool.remittance_tool.doctype.remittance_form_15_cb.remittance_form_15_cb.calculate_taxes_api",
		args: {
			doc: frm.doc,
		},
		callback: function (r) {
			if (r.message) {
				Object.assign(frm.doc, r.message);
				frm.refresh_fields();
			}
		},
	});
}
function show_approval_trail(frm) {
	frappe.call({
		method: "remittance_tool.remittance_tool.api.approval.approval_trail",
		args: { doctype: frm.doctype, doc_name: frm.doc.name },
		freeze: true,
		freeze_message: __("Loading approval trail..."),
		callback: function (r) {
			let data = r.message || {};
			let html = render_trail_html(data);

			let d = new frappe.ui.Dialog({
				title: __("Approval Trail — {0}", [frm.doc.name]),
				size: "extra-large",
				fields: [{ fieldtype: "HTML", fieldname: "trail_html" }],
			});
			d.fields_dict.trail_html.$wrapper.html(html);
			d.show();
		},
	});
}

function render_trail_html(data) {
	let stages = (data && data.stages) || [];
	if (!stages.length) {
		return `<div class="text-muted" style="padding:14px; font-size:13px;">
			${__("This document has not been submitted into the approval flow yet.")}
		</div>`;
	}

	let body_rows = [];
	stages.forEach((stage) => {
		let events = stage.events || [];
		events.forEach((ev, idx) => {
			let stage_cell = "";
			if (idx === 0) {
				stage_cell = `
					<td rowspan="${events.length}"
						style="vertical-align:top; font-weight:600; border-right:1px solid #ccc;">
						${__("Stage")} ${stage.stage}
						<br><small style="font-weight:400; color:#555;">
							${frappe.utils.escape_html(stage.stage_name || "")}
						</small>
					</td>`;
			}

			let who = ev.approver_name
				? `${frappe.utils.escape_html(ev.approver_name)}` +
				(ev.approver
					? `<br><small style="color:#666;">${frappe.utils.escape_html(
						ev.approver
					)}</small>`
					: "")
				: ev.approver_role
					? `<span style="color:#555;">${__("Role")}: ${frappe.utils.escape_html(
						ev.approver_role
					)}</span>`
					: "—";

			let when = ev.action_line
				? `<small>${frappe.utils.escape_html(ev.action_line)}</small>`
				: "—";

			let remarks = ev.remarks ? frappe.utils.escape_html(ev.remarks) : "—";

			body_rows.push(`
				<tr>
					${stage_cell}
					<td style="vertical-align:middle; font-weight:600;">${__(ev.label)}</td>
					<td style="vertical-align:middle;">${who}</td>
					<td style="vertical-align:middle;">${when}</td>
					<td style="vertical-align:middle;">${remarks}</td>
				</tr>
			`);
		});
	});

	return `
		<div style="border:1px solid #ccc; border-radius:4px; overflow:hidden; background:#fff;">
			<table class="table table-bordered"
				style="margin:0; font-size:13px; color:#000; background:#fff;">
				<thead style="background:#f0f0f0;">
					<tr>
						<th style="width:18%;">${__("Stage")}</th>
						<th style="width:22%;">${__("Status")}</th>
						<th style="width:20%;">${__("Approver")}</th>
						<th style="width:20%;">${__("When")}</th>
						<th>${__("Remarks")}</th>
					</tr>
				</thead>
				<tbody>${body_rows.join("")}</tbody>
			</table>
		</div>
	`;
}

function show_approval_details(frm) {
	frappe.call({
		method: "remittance_tool.remittance_tool.api.approval.approval_trail",
		args: { doctype: frm.doctype, doc_name: frm.doc.name },
		freeze: true,
		freeze_message: __("Loading..."),
		callback: function (r) {
			let data = r.message || {};
			let html = render_details_html(data);
			let d = new frappe.ui.Dialog({
				title: __("Approval Details"),
				size: "small",
				fields: [{ fieldtype: "HTML", fieldname: "details_html" }],
			});
			d.fields_dict.details_html.$wrapper.html(html);
			d.show();
		},
	});
}

// function render_details_html(data) {
// 	let stages = (data && data.stages) || [];
// 	if (!stages.length) {
// 		return `<div class="text-muted" style="padding:16px; font-size:13px;">
// 			${__("This document has not been submitted into the approval flow yet.")}
// 		</div>`;
// 	}

// 	const STATUS_PILL = {
// 		APPROVED:               { bg: "#d6f5dd", color: "#1e8449", border: "#27ae60" },
// 		REJECTED:               { bg: "#fbd6d6", color: "#a93226", border: "#c0392b" },
// 		"SENT BACK":            { bg: "#fde4c4", color: "#a35a00", border: "#e67e22" },
// 		"WAITING FOR APPROVAL": { bg: "#ffe9c4", color: "#a35a00", border: "#e67e22" },
// 		"PENDING APPROVAL":     { bg: "#ffe9c4", color: "#a35a00", border: "#e67e22" },
// 		"YET TO RECEIVE":       { bg: "#eee", color: "#666", border: "#bbb" },
// 	};

// 	const AVATAR_BG = {
// 		APPROVED: "#27ae60",
// 		REJECTED: "#c0392b",
// 		"SENT BACK": "#e67e22",
// 		"WAITING FOR APPROVAL": "#bdc3c7",
// 		"PENDING APPROVAL": "#bdc3c7",
// 		"YET TO RECEIVE": "#bdc3c7",
// 	};

// 	function initials(name) {
// 		if (!name) return "?";
// 		let parts = name.trim().split(/\s+/);
// 		if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
// 		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
// 	}

// 	function summarize_stage(stage) {
// 		let events = stage.events || [];
// 		if (!events.length) {
// 			return { label: "YET TO RECEIVE", approver_name: null, approver: null, submitted_on: null, acted_on: null };
// 		}
// 		let last = events[events.length - 1];
// 		let submitted = null, acted = null, acted_label = null;

// 		for (let i = events.length - 1; i >= 0; i--) {
// 			let e = events[i];
// 			if (e.label === "WAITING FOR APPROVAL" && e.action_line) {
// 				submitted = e.action_line;
// 				break;
// 			}
// 		}
// 		for (let i = events.length - 1; i >= 0; i--) {
// 			let e = events[i];
// 			if (e.label === "APPROVED" || e.label === "REJECTED" || e.label === "SENT BACK") {
// 				acted = e.action_line;
// 				acted_label = e.label;
// 				break;
// 			}
// 		}

// 		let display_label =
// 			acted_label ||
// 			(last.label === "WAITING FOR APPROVAL" ? "PENDING APPROVAL" : last.label);

// 		let approver_name = null, approver = null, approver_role = null;
// 		if (acted_label) {
// 			for (let i = events.length - 1; i >= 0; i--) {
// 				let e = events[i];
// 				if (e.label === acted_label) {
// 					approver_name = e.approver_name;
// 					approver = e.approver;
// 					approver_role = e.approver_role;
// 					break;
// 				}
// 			}
// 		} else {
// 			approver_name = last.approver_name;
// 			approver = last.approver;
// 			approver_role = last.approver_role;
// 		}

// 		return { label: display_label, approver_name, approver, approver_role, submitted_on: submitted, acted_on: acted };
// 	}

// 	let cards = stages.map((stage) => {
// 		let s = summarize_stage(stage);
// 		let pill = STATUS_PILL[s.label] || STATUS_PILL["YET TO RECEIVE"];
// 		let avatar_bg = AVATAR_BG[s.label] || "#bdc3c7";

// 		let display_name =
// 			s.approver_name ||
// 			(s.approver_role ? `${__("Role")}: ${s.approver_role}` : "—");
// 		let display_email = s.approver || "";

// 		let initials_text = initials(s.approver_name || s.approver_role || "?");

// 		let lines_html = "";
// 		if (s.submitted_on) {
// 			lines_html += `<div style="font-size:13px; color:#333;">${frappe.utils.escape_html(s.submitted_on)}</div>`;
// 		}
// 		if (s.acted_on) {
// 			lines_html += `<div style="font-size:13px; color:#333; margin-top:2px;">${frappe.utils.escape_html(s.acted_on)}</div>`;
// 		}
// 		if (!lines_html) {
// 			lines_html = `<div style="font-size:13px; color:#888;">${__("No activity yet")}</div>`;
// 		}

// 		return `
// 			<div style="margin-bottom:14px;">
// 				<div style="text-align:center; margin-bottom:6px;">
// 					<span style="
// 						background:${pill.bg};
// 						color:${pill.color};
// 						border:1px solid ${pill.border};
// 						padding:2px 12px;
// 						border-radius:12px;
// 						font-size:11px;
// 						font-weight:700;
// 						letter-spacing:0.4px;
// 						text-transform:uppercase;
// 					">${frappe.utils.escape_html(s.label)}</span>
// 				</div>
// 				<div style="
// 					border:1px solid #e5e5e5;
// 					border-radius:8px;
// 					padding:14px 16px;
// 					background:#fff;
// 					box-shadow:0 1px 2px rgba(0,0,0,0.04);
// 				">
// 					<div style="display:flex; align-items:center; gap:12px;">
// 						<div style="
// 							width:42px; height:42px; border-radius:50%;
// 							background:${avatar_bg};
// 							color:#fff; font-weight:700; font-size:14px;
// 							display:flex; align-items:center; justify-content:center;
// 							flex:0 0 42px;
// 						">${frappe.utils.escape_html(initials_text)}</div>
// 						<div style="min-width:0; flex:1;">
// 							<div style="font-weight:600; font-size:14px; color:#222; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
// 								${frappe.utils.escape_html(display_name)}
// 							</div>
// 							<div style="font-size:12px; color:#777; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
// 								${frappe.utils.escape_html(display_email)}
// 							</div>
// 						</div>
// 					</div>
// 					<div style="margin-top:10px; padding-top:10px; border-top:1px solid #f0f0f0;">
// 						${lines_html}
// 					</div>
// 				</div>
// 				<div style="
// 					height:14px;
// 					margin-top:-2px;
// 					background-image: linear-gradient(45deg, transparent 50%, ${pill.border} 50%),
// 									  linear-gradient(-45deg, transparent 50%, ${pill.border} 50%);
// 					background-size: 12px 14px;
// 					background-position: left top, right top;
// 					background-repeat: no-repeat;
// 					opacity:0.55;
// 				"></div>
// 			</div>
// 		`;
// 		})
// 		.join("");

// 	return `<div style="padding:6px;">${cards}</div>`;
// }

function render_details_html(data) {
	let stages = (data && data.stages) || [];
	if (!stages.length) {
		return `<div class="text-muted" style="padding:16px; font-size:13px;">
			${__("This document has not been submitted into the approval flow yet.")}
		</div>`;
	}

	const STATUS_PILL_CLASS = {
		APPROVED: "pill-approved",
		REJECTED: "pill-rejected",
		"SENT BACK": "pill-sentback",
		"WAITING FOR APPROVAL": "pill-pending",
		"PENDING APPROVAL": "pill-pending",
		"YET TO RECEIVE": "pill-yet",
	};

	const AVATAR_CLASS = {
		APPROVED: "av-approved",
		REJECTED: "av-rejected",
		"SENT BACK": "av-sentback",
		"WAITING FOR APPROVAL": "av-yet",
		"PENDING APPROVAL": "av-pending",
		"YET TO RECEIVE": "av-yet",
	};

	function initials(name) {
		if (!name) return "?";
		let parts = name.trim().split(/\s+/);
		if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
	}

	function extract_date(action_line) {
		if (!action_line) return null;
		// Matches patterns like "29-04-2026 15:53" or "29-04-2026"
		let match = action_line.match(/(\d{2}-\d{2}-\d{4}(?:\s+\d{2}:\d{2})?)/);
		return match ? match[1] : action_line;
	}

	function summarize_stage(stage) {
		let events = stage.events || [];
		if (!events.length) {
			return {
				label: "YET TO RECEIVE",
				approver_name: null,
				approver: null,
				approver_role: null,
				submitted_on: null,
				acted_on: null,
			};
		}

		let last = events[events.length - 1];
		let submitted = null,
			acted = null,
			acted_label = null;

		for (let i = events.length - 1; i >= 0; i--) {
			let e = events[i];
			if (e.label === "WAITING FOR APPROVAL" && e.action_line) {
				submitted = e.action_line;
				break;
			}
		}
		for (let i = events.length - 1; i >= 0; i--) {
			let e = events[i];
			if (e.label === "APPROVED" || e.label === "REJECTED" || e.label === "SENT BACK") {
				acted = e.action_line;
				acted_label = e.label;
				break;
			}
		}

		let display_label =
			acted_label ||
			(last.label === "WAITING FOR APPROVAL" ? "PENDING APPROVAL" : last.label);

		let approver_name = null,
			approver = null,
			approver_role = null;
		if (acted_label) {
			for (let i = events.length - 1; i >= 0; i--) {
				let e = events[i];
				if (e.label === acted_label) {
					approver_name = e.approver_name;
					approver = e.approver;
					approver_role = e.approver_role;
					break;
				}
			}
		} else {
			approver_name = last.approver_name;
			approver = last.approver;
			approver_role = last.approver_role;
		}

		return {
			label: display_label,
			approver_name,
			approver,
			approver_role,
			submitted_on: submitted,
			acted_on: acted,
		};
	}

	const css = `
		<style>
			.af-card {
				background: #fff;
				border: 1px solid #e8e8e8;
				border-radius: 8px;
				padding: 12px 14px;
				margin-bottom: 10px;
			}
			.af-header {
				display: flex;
				align-items: center;
				justify-content: space-between;
				margin-bottom: 10px;
			}
			.af-stage { font-size: 11px; color: #aaa; }
			.af-pill {
				display: inline-flex;
				align-items: center;
				padding: 2px 9px;
				border-radius: 20px;
				font-size: 11px;
				font-weight: 600;
				letter-spacing: 0.3px;
				text-transform: uppercase;
			}
			.pill-approved { background: #d6f5dd; color: #1e7e34; }
			.pill-rejected { background: #fbd6d6; color: #a93226; }
			.pill-sentback { background: #fde4c4; color: #a35a00; }
			.pill-pending  { background: #fff3cd; color: #856404; }
			.pill-yet      { background: #f0f0f0; color: #888;    }
			.af-body {
				display: flex;
				align-items: center;
				gap: 10px;
			}
			.af-avatar {
				width: 36px;
				height: 36px;
				border-radius: 50%;
				display: flex;
				align-items: center;
				justify-content: center;
				font-size: 12px;
				font-weight: 600;
				flex: 0 0 36px;
			}
			.av-approved { background: #d6f5dd; color: #1e7e34; }
			.av-rejected { background: #fbd6d6; color: #a93226; }
			.av-sentback { background: #fde4c4; color: #a35a00; }
			.av-pending  { background: #fff3cd; color: #856404; }
			.av-yet      { background: #f0f0f0; color: #888;    }
			.af-left {
				flex: 1;
				min-width: 0;
			}
			.af-name {
				font-size: 13px;
				font-weight: 600;
				color: #222;
				white-space: nowrap;
				overflow: hidden;
				text-overflow: ellipsis;
			}
			.af-email {
				font-size: 11px;
				color: #888;
				white-space: nowrap;
				overflow: hidden;
				text-overflow: ellipsis;
			}
			.af-right {
				display: flex;
				gap: 12px;
				align-items: flex-end;
				flex: 0 0 auto;
			}
			.af-meta {
				display: flex;
				flex-direction: column;
				align-items: flex-end;
				gap: 2px;
			}
			.af-meta-label {
				font-size: 10px;
				color: #bbb;
				line-height: 1;
				white-space: nowrap;
			}
			.af-meta-value {
				font-size: 11px;
				font-weight: 600;
				color: #444;
				text-align: right;
				line-height: 1.3;
				white-space: nowrap;
			}
			.af-meta-empty { color: #ccc; font-weight: 400; }
			.af-sep {
				width: 1px;
				height: 28px;
				background: #ececec;
				align-self: center;
			}
		</style>
	`;

	let cards = stages
		.map((stage, idx) => {
			let s = summarize_stage(stage);
			let pill_class = STATUS_PILL_CLASS[s.label] || "pill-yet";
			let avatar_class = AVATAR_CLASS[s.label] || "av-yet";

			let display_name =
				s.approver_name || (s.approver_role ? `${__("Role")}: ${s.approver_role}` : "—");
			let display_email = s.approver || "";
			let initials_text = initials(s.approver_name || s.approver_role || "?");

			let submitted_date = extract_date(s.submitted_on);
			let acted_date = extract_date(s.acted_on);

			let submitted_html = `
			<div class="af-meta">
				<span class="af-meta-label">${__("Submitted on")}</span>
				${submitted_date
					? `<span class="af-meta-value">${frappe.utils.escape_html(
						submitted_date
					)}</span>`
					: `<span class="af-meta-value af-meta-empty">—</span>`
				}
			</div>`;

			let acted_html = `
			<div class="af-meta">
				<span class="af-meta-label">${__("Acted on")}</span>
				${acted_date
					? `<span class="af-meta-value">${frappe.utils.escape_html(
						acted_date
					)}</span>`
					: `<span class="af-meta-value af-meta-empty">—</span>`
				}
			</div>`;

			return `
			<div class="af-card">
				<div class="af-header">
					<span class="af-stage">${__("Stage")} ${idx + 1}</span>
					<span class="af-pill ${pill_class}">${frappe.utils.escape_html(s.label)}</span>
				</div>
				<div class="af-body">
					<div class="af-avatar ${avatar_class}">
						${frappe.utils.escape_html(initials_text)}
					</div>
					<div class="af-left">
						<div class="af-name">${frappe.utils.escape_html(display_name)}</div>
						<div class="af-email">${frappe.utils.escape_html(display_email)}</div>
					</div>
					<div class="af-right">
						${submitted_html}
						<div class="af-sep"></div>
						${acted_html}
					</div>
				</div>
			</div>`;
		})
		.join("");

	return `${css}<div style="padding:4px;">${cards}</div>`;
}

function approve_reject_dialog(frm, action) {
	// Backward compat: accept boolean (true = Approve, false = Reject)
	if (action === true) action = "Approve";
	else if (action === false) action = "Reject";

	if (action === "SendBack") {
		return send_back_dialog(frm);
	}

	const config = {
		Approve: {
			title: __("Approve"),
			method: "remittance_tool.remittance_tool.api.approval.approve",
			freeze_message: __("Approving..."),
			indicator: "green",
			reqd: 0,
		},
		Reject: {
			title: __("Reject"),
			method: "remittance_tool.remittance_tool.api.approval.reject",
			freeze_message: __("Rejecting..."),
			indicator: "red",
			reqd: 1,
		},
	}[action];

	if (!config) return;

	let d = new frappe.ui.Dialog({
		title: config.title,
		fields: [
			{
				label: __("Remarks"),
				fieldname: "remarks",
				fieldtype: "Small Text",
				reqd: config.reqd,
			},
		],
		primary_action_label: config.title,
		primary_action(values) {
			frappe.call({
				method: config.method,
				args: {
					doctype: frm.doctype,
					doc_name: frm.doc.name,
					remarks: values.remarks || "",
				},
				freeze: true,
				freeze_message: config.freeze_message,
				callback: function (r) {
					d.hide();
					if (r.message) {
						frappe.show_alert({
							message: r.message.message || "",
							indicator: config.indicator,
						});
					}
					frm.reload_doc();
				},
			});
		},
	});
	d.show();
}

function send_back_dialog(frm) {
	// First fetch the candidates (Maker + previous approvers), then show a dialog
	frappe.call({
		method: "remittance_tool.remittance_tool.api.approval.send_back_candidates",
		args: { doctype: frm.doctype, doc_name: frm.doc.name },
		freeze: true,
		freeze_message: __("Loading candidates..."),
		callback: function (r) {
			const candidates = r.message || [];
			if (!candidates.length) {
				frappe.msgprint(__("No candidate found to send this document back to."));
				return;
			}

			const select_options = candidates.map((c) => c.user).join("\n");

			let d = new frappe.ui.Dialog({
				title: __("Send Back"),
				fields: [
					{
						label: __("Send Back To"),
						fieldname: "target_user",
						fieldtype: "Select",
						options: select_options,
						default: candidates[0].user,
						reqd: 1,
						description: candidates
							.map((c) => `• <b>${c.user}</b> — ${c.label}`)
							.join("<br>"),
					},
					{
						label: __("Remarks"),
						fieldname: "remarks",
						fieldtype: "Small Text",
						reqd: 1,
					},
				],
				primary_action_label: __("Send Back"),
				primary_action(values) {
					frappe.call({
						method: "remittance_tool.remittance_tool.api.approval.send_back",
						args: {
							doctype: frm.doctype,
							doc_name: frm.doc.name,
							remarks: values.remarks || "",
							target_user: values.target_user,
						},
						freeze: true,
						freeze_message: __("Sending back..."),
						callback: function (resp) {
							d.hide();
							if (resp.message) {
								frappe.show_alert({
									message: resp.message.message || "",
									indicator: "orange",
								});
							}
							frm.reload_doc();
						},
					});
				},
			});
			d.show();
		},
	});
}

function set_fields_readonly(frm) {
	// Post-approval fields MUST stay editable so the user can upload
	// supporting documents and add a remark after approval.
	const POST_APPROVAL_EDITABLE = new Set([
		"attachments",                 // child table of files
		"post_approval_remark",         // Small Text remark
		"section_break_jeps",           // the section break holding these
		"post_approval_section",        // (if used in some doctype versions)
	]);

	// Don't disable save anymore — user needs to save attachments / remark.
	// Instead, leave save enabled but make non-whitelisted fields readonly.

	// Make all non-whitelisted fields readonly
	frm.fields.forEach((field) => {
		const fname = field.df.fieldname;
		if (!fname) return;
		if (POST_APPROVAL_EDITABLE.has(fname)) return;
		frm.set_df_property(fname, "read_only", 1);
	});

	// Disable add/remove row controls on child tables — EXCEPT post-approval
	// ones (e.g. attachments) where user needs to add files
	frm.fields.forEach((field) => {
		if (field.df.fieldtype !== "Table") return;
		if (POST_APPROVAL_EDITABLE.has(field.df.fieldname)) return; // keep editable

		const grid = frm.get_field(field.df.fieldname).grid;
		grid.wrapper.find(".grid-add-row").hide();
		grid.wrapper.find(".grid-remove-rows").hide();
		grid.wrapper.find(".grid-remove-all-rows").hide();
	});
}

// ─── Snapshot fields: visible but non-editable ──────────────────────────
// Vendor / Company / CA Details tabs me fields fetch_from se auto-populate
// hote hain. Yahan har refresh / link-change ke baad DOM-level readonly
// apply karte hain — Frappe ke "hide empty read_only field" behaviour ko
// trigger kiye bina field locked + visible rakhne ke liye.

function lock_fetched_snapshot_fields(frm) {
	const prefixes = ["v_", "c_", "ca_"];
	const exclude = new Set([
		// Tab/section/column break-likes are unaffected, but tab field names
		// themselves (e.g. ca_details_tab) shouldn't be touched.
		"vendor_details_tab",
		"company_details_tab",
		"ca_details_tab",
	]);

	Object.keys(frm.fields_dict).forEach(function (fname) {
		if (exclude.has(fname)) return;
		if (!prefixes.some((p) => fname.startsWith(p))) return;

		const field = frm.fields_dict[fname];
		if (!field || !field.$input) return;

		// `readonly` (HTML attribute) keeps the value in the submitted form
		// but prevents user edits. `disabled` would strip the value — don't use.
		field.$input.prop("readonly", true);
		field.$input.attr("tabindex", "-1");
		field.$input.css({
			"background-color": "#f7f7f7",
			cursor: "not-allowed",
		});
	});
}

frappe.ui.form.on("Remittance Form 15 CB", {
	refresh: function (frm) {
		// Run after Frappe finishes its own refresh-time field rendering.
		setTimeout(() => lock_fetched_snapshot_fields(frm), 200);
	},
	vendor: function (frm) {
		// Re-lock after Frappe auto-fetches new vendor values.
		setTimeout(() => lock_fetched_snapshot_fields(frm), 400);
	},
	company: function (frm) {
		setTimeout(() => lock_fetched_snapshot_fields(frm), 400);
	},
	ca: function (frm) {
		setTimeout(() => lock_fetched_snapshot_fields(frm), 400);
	},
});

// ─── Send Email dialog (multi-recipient) ────────────────────────────────
// Recipients are decided by the user at send time. Default suggestions are
// pulled from the backend (Maker, CA, Company, Vendor). User can edit /
// add / remove before sending.

function open_send_email_dialog(frm) {
	frappe.call({
		method: "remittance_tool.remittance_tool.api.email_sender.suggest_recipients",
		args: { docname: frm.doc.name },
		callback: function (r) {
			const suggestions = (r.message && r.message.suggestions) || [];
			const default_to = suggestions.map((s) => s.email).join(", ");
			const suggestion_html = suggestions.length
				? `<div style="margin-top:6px; font-size:11px; color:#64748b;">
				    <strong>Suggested:</strong><br>
				    ${suggestions.map((s) => `<span style="display:inline-block; padding:2px 6px; background:#f1f5f9; border-radius:3px; margin:2px;">${frappe.utils.escape_html(s.label)}</span>`).join(" ")}
				   </div>`
				: "";

			const dialog = new frappe.ui.Dialog({
				title: __("Send Form 15CB by Email"),
				size: "large",
				fields: [
					{
						fieldname: "recipients",
						fieldtype: "Small Text",
						label: __("To (comma-separated)"),
						reqd: 1,
						default: default_to,
						description: __(
							"Add one or more email addresses, separated by commas. Suggestions below."
						),
					},
					{
						fieldname: "recipients_html",
						fieldtype: "HTML",
						options: suggestion_html,
					},
					{
						fieldname: "cc",
						fieldtype: "Data",
						label: __("Cc"),
					},
					{
						fieldname: "bcc",
						fieldtype: "Data",
						label: __("Bcc"),
					},
					{
						fieldname: "subject",
						fieldtype: "Data",
						label: __("Subject"),
						default: `Form 15CB - ${frm.doc.name}`,
					},
					{
						fieldname: "message",
						fieldtype: "Text Editor",
						label: __("Message"),
						default: build_default_message(frm),
					},
					{
						fieldname: "attach_section",
						fieldtype: "Section Break",
						label: __("Attachments"),
					},
					{
						fieldname: "attach_json",
						fieldtype: "Check",
						label: __("Attach JSON"),
						default: 1,
					},
					{
						fieldname: "attach_xml",
						fieldtype: "Check",
						label: __("Attach XML"),
						default: 1,
					},
				],
				primary_action_label: __("Send"),
				primary_action: function (values) {
					frappe.call({
						method: "remittance_tool.remittance_tool.api.email_sender.send_form_15cb_email",
						args: {
							docname: frm.doc.name,
							recipients: values.recipients,
							cc: values.cc || "",
							bcc: values.bcc || "",
							subject: values.subject,
							message: values.message,
							attach_json: values.attach_json ? 1 : 0,
							attach_xml: values.attach_xml ? 1 : 0,
						},
						freeze: true,
						freeze_message: __("Sending email..."),
						callback: function (resp) {
							if (resp.message && resp.message.status === "success") {
								frappe.show_alert({
									message: resp.message.message,
									indicator: "green",
								});
								dialog.hide();
							}
						},
					});
				},
			});

			dialog.show();
		},
	});
}

function build_default_message(frm) {
	const remark = (frm.doc.post_approval_remark || "").trim();
	const remark_html = remark
		? `<p><strong>Remark:</strong> ${frappe.utils.escape_html(remark)}</p>`
		: "";
	const vendor = frm.doc.vendor || "";
	return `
		<p>Dear Sir/Madam,</p>
		<p>Please find attached the Form 15CB <strong>${frappe.utils.escape_html(frm.doc.name)}</strong>
		for vendor <strong>${frappe.utils.escape_html(vendor)}</strong>.</p>
		${remark_html}
		<p>Regards,<br>Remittance Tool</p>
	`;
}

// ─── Send JSON to CA dialog ─────────────────────────────────────────────
// Opens a small sub-dialog with a CA Master selector. On confirm, emails
// the rendered JSON to the chosen CA's email_id.

function open_send_json_to_ca_dialog(frm) {
	const default_ca = frm.doc.ca || null;

	const dialog = new frappe.ui.Dialog({
		title: __("Send JSON to CA"),
		size: "small",
		fields: [
			{
				fieldname: "ca",
				fieldtype: "Link",
				label: __("Select CA"),
				options: "CA Master",
				reqd: 1,
				default: default_ca,
				description: __("CA's email_id will be auto-fetched and the JSON will be sent there."),
			},
			{
				fieldname: "ca_email_preview",
				fieldtype: "Data",
				label: __("CA Email"),
				read_only: 1,
				description: __("Auto-filled from CA Master once a CA is selected."),
			},
			{
				fieldname: "message",
				fieldtype: "Text Editor",
				label: __("Message (optional)"),
				description: __("Leave blank to use the default template."),
			},
		],
		primary_action_label: __("Send JSON"),
		primary_action: function (values) {
			if (!values.ca) {
				frappe.msgprint(__("Please select a CA first."));
				return;
			}
			frappe.call({
				method: "remittance_tool.remittance_tool.api.email_sender.send_json_to_ca",
				args: {
					docname: frm.doc.name,
					ca_name: values.ca,
					message: values.message || "",
				},
				freeze: true,
				freeze_message: __("Sending JSON to CA..."),
				callback: function (r) {
					if (r.message && r.message.status === "success") {
						frappe.show_alert({
							message: __("JSON sent to {0}", [r.message.ca_email]),
							indicator: "green",
						});
						dialog.hide();
					}
				},
			});
		},
	});

	// When CA is selected, fetch + preview its email
	dialog.fields_dict.ca.df.onchange = function () {
		const ca_name = dialog.get_value("ca");
		if (!ca_name) {
			dialog.set_value("ca_email_preview", "");
			return;
		}
		frappe.db.get_value("CA Master", ca_name, ["email_id", "ca_name"]).then((r) => {
			const email = r.message?.email_id || "";
			dialog.set_value("ca_email_preview", email);
			if (!email) {
				frappe.show_alert({
					message: __("Selected CA has no email_id set."),
					indicator: "orange",
				});
			}
		});
	};

	dialog.show();

	// Pre-fill email preview if a default CA was linked
	if (default_ca) {
		setTimeout(() => dialog.fields_dict.ca.df.onchange(), 200);
	}
}


// ─── Send Documents (attachments + remark + multi-recipient) ─────────────
// Opens a dialog where the user:
//   - sees all files attached to the form (with checkboxes)
//   - can upload more files INLINE (Frappe FileUploader)
//   - picks recipients via User dropdown — emails get added as chips
//   - adds a remark (HTML body)
//   - sends — selected attachments go to all recipients

function open_send_attachments_dialog(frm) {
	frappe.call({
		method: "remittance_tool.remittance_tool.api.email_sender.list_form_attachments",
		args: { docname: frm.doc.name },
		callback: function (r) {
			const files = r.message || [];
			open_attachments_dialog_with_files(frm, files);
		},
	});
}

function open_attachments_dialog_with_files(frm, files) {
	const dialog = new frappe.ui.Dialog({
		title: __("Send Documents — {0}", [frm.doc.name]),
		size: "large",
		fields: [
			{
				fieldname: "to",
				fieldtype: "MultiSelectList",
				label: __("To"),
				reqd: 1,
				get_data: function (txt) {
					return frappe.db.get_link_options("User", txt);
				},
			},
			{
				fieldname: "recipient_list",
				fieldtype: "HTML",
				options: `<div id="atc-emails" style="margin:-6px 0 10px; padding:8px 12px; background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px; font-size:12px; color:#1e40af; min-height:32px;">
					<span style="color:#94a3b8; font-style:italic;">No recipients yet</span>
				</div>`,
			},
			{
				fieldname: "subject",
				fieldtype: "Data",
				label: __("Subject"),
				default: `Form 15CB - ${frm.doc.name} - Documents`,
			},
			{
				fieldname: "files_section",
				fieldtype: "Section Break",
				label: __("Attachments"),
			},
			{
				fieldname: "files_html_field",
				fieldtype: "HTML",
				options: build_files_html(files),
			},
			{
				fieldname: "upload_btn",
				fieldtype: "Button",
				label: __("⬆ Upload File"),
			},
			{
				fieldname: "message_section",
				fieldtype: "Section Break",
				label: __("Remark"),
			},
			{
				fieldname: "message",
				fieldtype: "Small Text",
				label: __("Remark"),
				default: frm.doc.post_approval_remark || "",
			},
		],
		primary_action_label: __("Send"),
		primary_action: function (values) {
			const recipients = (values.to || []).filter((e) => /\S+@\S+\.\S+/.test(e));
			if (!recipients.length) {
				frappe.msgprint(__("Please pick at least one recipient."));
				return;
			}

			const ticked_urls = [];
			dialog.$wrapper.find("input.atc-file:checked").each(function () {
				ticked_urls.push($(this).val());
			});
			if (!ticked_urls.length && files.length) {
				frappe.msgprint(__("Please select at least one file to attach."));
				return;
			}

			frappe.call({
				method: "remittance_tool.remittance_tool.api.email_sender.send_attachments_email",
				args: {
					docname: frm.doc.name,
					recipients: recipients.join(","),
					cc: "",
					file_urls: ticked_urls,
					subject: values.subject,
					message: values.message || "",
				},
				freeze: true,
				freeze_message: __("Sending email..."),
				callback: function (r) {
					if (r.message && r.message.status === "success") {
						frappe.show_alert({
							message: r.message.message,
							indicator: "green",
						});
						dialog.hide();
					}
				},
			});
		},
	});

	dialog.show();

	// Live email list — shows the actual selected addresses
	const update_emails = () => {
		const list = (dialog.get_value("to") || []).filter(Boolean);
		const $box = dialog.$wrapper.find("#atc-emails");
		if (!list.length) {
			$box.html('<span style="color:#94a3b8; font-style:italic;">No recipients yet</span>');
			$box.css({ background: "#eff6ff", border: "1px solid #bfdbfe" });
			return;
		}
		const chips = list
			.map((e) => `<span style="display:inline-block; margin:2px 4px 2px 0; padding:3px 8px; background:#ffffff; border:1px solid #86efac; border-radius:12px; font-weight:500; color:#166534;">${frappe.utils.escape_html(e)}</span>`)
			.join("");
		$box.html(chips);
		$box.css({ background: "#dcfce7", border: "1px solid #86efac" });
	};
	if (dialog.fields_dict.to && dialog.fields_dict.to.df) {
		dialog.fields_dict.to.df.onchange = update_emails;
	}
	const _email_poll = setInterval(update_emails, 400);
	dialog.$wrapper.on("hidden.bs.modal", function () {
		clearInterval(_email_poll);
	});

	// Inline Upload File button — saves to form's attachments table
	dialog.fields_dict.upload_btn.$wrapper.find("button").on("click", function () {
		new frappe.ui.FileUploader({
			doctype: "Remittance Form 15 CB",
			docname: frm.doc.name,
			on_success: function (file_doc) {
				const file_url = file_doc.file_url;
				frappe.call({
					method: "remittance_tool.remittance_tool.api.email_sender.add_attachment_to_form",
					args: { docname: frm.doc.name, file_url: file_url },
					callback: function (r) {
						if (!r.message) return;
						frappe.show_alert({
							message: __("Uploaded: {0}", [file_doc.file_name]),
							indicator: "green",
						});
						frappe.call({
							method: "remittance_tool.remittance_tool.api.email_sender.list_form_attachments",
							args: { docname: frm.doc.name },
							callback: function (r2) {
								const new_files = r2.message || [];
								dialog.fields_dict.files_html_field.$wrapper.html(build_files_html(new_files));
								files.length = 0;
								new_files.forEach((f) => files.push(f));
							},
						});
						frm.reload_doc();
					},
				});
			},
		});
	});
}

function build_files_html(files) {
	if (!files.length) {
		return `<p style="margin:8px 0; color:#94a3b8; font-size:13px;">
			${__("No attachments in the form's Attachments table. Add files in the Attachments section of Form 15CB (visible after Approval).")}
		</p>`;
	}
	return `
		<div style="border:1px solid #e2e8f0; border-radius:8px; padding:12px 16px; max-height:240px; overflow-y:auto; background:#f8fafc;">
			<div style="margin-bottom:8px; font-size:11px; font-weight:600; text-transform:uppercase; color:#64748b; letter-spacing:0.05em;">
				${__("Select Files to Attach")} (${files.length})
			</div>
			${files
				.map(
					(f) => `
				<label style="display:block; padding:6px 0; cursor:pointer; font-size:13px; color:#1a202c; border-bottom:1px solid #f1f5f9;">
					<input type="checkbox" class="atc-file" value="${frappe.utils.escape_html(f.file_url)}" checked style="margin-right:8px;">
					<span style="font-weight:500;">📎 ${frappe.utils.escape_html(f.file_name)}</span>
					<small style="color:#94a3b8; margin-left:8px;">${frappe.utils.escape_html(f.size_label)}</small>
					${f.missing ? '<span style="color:#dc2626; margin-left:8px; font-size:11px;">⚠ FILE MISSING</span>' : ''}
				</label>
			`
				)
				.join("")}
		</div>
	`;
}



// ─── Universal "copy to clipboard" ──────────────────────────────────────
// navigator.clipboard.writeText() requires a SECURE context (HTTPS or
// localhost). UAT runs on http://10.10.3.143:96 — non-secure — so the
// modern API throws / is undefined. Fall back to the legacy execCommand
// approach which works on plain HTTP too.

function copy_text_to_clipboard(text) {
	// Path 1: Modern Clipboard API (HTTPS / localhost only)
	if (navigator.clipboard && window.isSecureContext) {
		navigator.clipboard.writeText(text).then(
			function () {
				frappe.show_alert({ message: __("Copied to clipboard"), indicator: "green" });
			},
			function (err) {
				_legacy_clipboard_copy(text);
			}
		);
		return;
	}

	// Path 2: Legacy fallback for http:// + LAN IP contexts (UAT)
	_legacy_clipboard_copy(text);
}

function _legacy_clipboard_copy(text) {
	// Create an off-screen textarea, select its contents, exec copy command.
	const ta = document.createElement("textarea");
	ta.value = text;
	// Make sure it's off-screen and won't scroll the page
	ta.style.position = "fixed";
	ta.style.top = "-9999px";
	ta.style.left = "-9999px";
	ta.style.opacity = "0";
	ta.setAttribute("readonly", "");
	document.body.appendChild(ta);

	let succeeded = false;
	try {
		ta.select();
		ta.setSelectionRange(0, ta.value.length);
		succeeded = document.execCommand("copy");
	} catch (e) {
		succeeded = false;
	} finally {
		document.body.removeChild(ta);
	}

	if (succeeded) {
		frappe.show_alert({ message: __("Copied to clipboard"), indicator: "green" });
	} else {
		// Last resort: show a modal so the user can manually Ctrl+C
		const d = new frappe.ui.Dialog({
			title: __("Copy manually (Ctrl+C / Cmd+C)"),
			size: "large",
			fields: [
				{
					fieldname: "manual_copy",
					fieldtype: "Code",
					label: __("Select all (Ctrl+A) then copy (Ctrl+C)"),
					default: text,
				},
			],
		});
		d.show();
		setTimeout(() => {
			const $ta = d.$wrapper.find("textarea");
			if ($ta.length) {
				$ta[0].focus();
				$ta[0].select();
			}
		}, 200);
	}
}
