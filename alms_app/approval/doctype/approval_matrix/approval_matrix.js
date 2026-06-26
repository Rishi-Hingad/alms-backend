frappe.ui.form.on("Approval Matrix", {
	refresh: function (frm) {
		// Hide legacy conditions table
		frm.set_df_property("conditions", "hidden", 1);

		// Auto-load on refresh if already selected
		if (frm.doc.applies_to_doctype) {
			frm.trigger("applies_to_doctype");
		}


	},

	applies_to_doctype: function (frm) {
		if (!frm.doc.applies_to_doctype) return;

		// Load metadata for the selected Doctype
		frappe.model.with_doctype(frm.doc.applies_to_doctype, () => {
			// Filter valid fields (no breaks, no HTML, no Tables)
			const fields = frappe.meta
				.get_docfields(frm.doc.applies_to_doctype)
				.filter(
					(df) =>
						df.fieldname &&
						!df.hidden &&
						![
							"Section Break",
							"Column Break",
							"Tab Break",
							"HTML",
							"Button",
							"Table",
						].includes(df.fieldtype)
				);

			// Store fields for later lookup
			frm._applies_to_fields = fields;

			// Populate child table fields for status and remarks mapping
			let field_options = ["", ...fields.map(df => df.fieldname)];
			frm.fields_dict.approval_stages.grid.update_docfield_property("status_field", "options", field_options);
			frm.fields_dict.approval_stages.grid.update_docfield_property("remarks_field", "options", field_options);

			frm.trigger("set_up_filters_editor");
		});
	},

	set_up_filters_editor: function (frm) {
		const field = frm.get_field("filter_area");
		if (!field) return;

		// Inject Custom CSS for Modern UI
		const css = `
			<style>
				/* Main Container */
				.filter-group-container {
					background-color: var(--card-bg);
					border: 1px solid var(--border-color);
					border-radius: 12px;
					padding: 24px;
					margin-top: 16px;
					box-shadow: var(--shadow-xs);
				}

				/* Header Section */
				.filter-group-header {
					margin-bottom: 20px;
					display: flex;
					justify-content: flex-start; /* Force left align */
					align-items: flex-start;
					text-align: left;
				}

				.filter-group-title {
					font-size: 15px;
					font-weight: 600;
					color: var(--heading-color);
					margin-bottom: 4px;
				}

				.filter-group-subtitle {
					font-size: 13px;
					color: var(--text-muted);
					line-height: 1.5;
				}

				/* Filter Rows (Cards) */
				.filter-group-container .filter-box {
					background-color: var(--bg-light-gray); /* Subtle contrast against card bg */
					border: 1px solid transparent;
					border-radius: 8px;
					padding: 12px;
					margin-bottom: 12px;
					display: flex;
					align-items: center;
					justify-content: flex-start; /* Force left alignment */
					gap: 12px;
					transition: all 0.2s ease;
					width: 100%; /* Ensure full width */
				}

				.filter-group-container .filter-box:hover {
					background-color: var(--bg-light-gray) !important;
					border-color: transparent !important;
					box-shadow: none !important;
					transform: none !important;
				}



				/* Override Frappe defaults */
				.filter-group-container .filter-box {
					border-bottom: 1px solid transparent !important;
				}

				/* Column Widths - Adjusted to fill space */
				.filter-group-container .filter-box .filter-field {
					flex: 0 0 30% !important; /* Increased width */
					min-width: 0;
					margin: 0 !important;
				}

				.filter-group-container .filter-box .filter-operator {
					flex: 0 0 20% !important;
					min-width: 0;
					margin: 0 !important;
				}

				.filter-group-container .filter-box .filter-value {
					flex: 1 !important; /* Take remaining space */
					min-width: 0;
					margin: 0 !important;
				}

				/* Remove Button Container */
				.filter-group-container .filter-box .remove-filter {
					flex: 0 0 auto;
					margin-left: auto !important;
				}

				/* Input Fields - Force full width */
				.filter-group-container .form-control {
					background-color: var(--card-bg);
					border: 1px solid var(--border-color);
					border-radius: 6px;
					height: 36px; /* Slightly taller for better touch/click */
					font-size: 13px;
					color: var(--text-color);
					box-shadow: none;
					transition: border-color 0.2s, box-shadow 0.2s;
					width: 100% !important;
					max-width: 100% !important;
				}

				.filter-group-container .form-control:focus {
					border-color: var(--primary);
					box-shadow: 0 0 0 3px var(--primary-light);
					background-color: var(--card-bg);
				}

				.filter-group-container .form-control:hover {
					border-color: var(--gray-400);
				}

				/* Remove Button */
				.filter-group-container .remove-filter {
					color: var(--text-muted);
					cursor: pointer;
					padding: 8px;
					border-radius: 6px;
					transition: all 0.2s;
					opacity: 0.7;
					display: flex;
					align-items: center;
					justify-content: center;
					background: transparent;
					border: none;
					box-shadow: none;
					margin-left: auto;
				}

				.filter-group-container .remove-filter:hover {
					background-color: var(--bg-red-light);
					color: var(--red-500);
					opacity: 1;
				}

				.filter-group-container .remove-filter svg {
					width: 16px;
					height: 16px;
				}

				/* Actions Footer */
				.filter-group-container .filter-actions {
					display: flex;
					justify-content: space-between;
					align-items: center;
					margin-top: 24px;
					padding-top: 16px;
					border-top: 1px solid var(--border-color);
				}

				/* Add Filter Button - Specific Targeting */
				button.add-filter.btn {
					background-color: var(--primary);
					color: white !important;
					padding: 8px 16px;
					border-radius: 8px;
					font-weight: 500;
					font-size: 13px;
					display: inline-flex;
					align-items: center;
					gap: 8px;
					transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
					text-decoration: none;
					border: 1px solid transparent;
					box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
				}

				/* Ensure no double plus */
				button.add-filter.btn::before {
					content: none !important;
					display: none !important;
				}

				button.add-filter.btn:hover {
					background-color: var(--primary) !important;
					color: white !important;
					box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
					transform: none !important;
					text-decoration: none;
				}

				/* Clear Filters Button */
				.filter-group-container .clear-filters {
					color: var(--text-muted);
					font-size: 13px;
					padding: 8px 16px;
					border-radius: 8px;
					transition: all 0.2s;
					background: transparent;
					border: 1px solid transparent;
					font-weight: 500;
				}

				.filter-group-container .clear-filters:hover {
					background-color: var(--bg-light-gray);
					color: var(--text-color);
				}
			</style>
		`;

		// Use a dedicated container to avoid issues with parent.empty() not cleaning up FilterGroup artifacts completely
		if (field.$wrapper.find(".filter-group-container").length === 0) {
			field.$wrapper.html(`
				${css}
				<div class="filter-group-container">
					<div class="filter-group-header">
						<div>
							<div class="filter-group-title">
								${frappe.utils.icon("filter", "sm")}
								<span style="padding-left: 8px;">Filter Conditions</span>
							</div>
							<div class="filter-group-subtitle">
								Define the conditions that must be met for this policy to apply.
							</div>
						</div>
					</div>
					<div class="filter-group-body"></div>
				</div>
			`);
		}
		const parent = field.$wrapper.find(".filter-group-body");
		parent.empty();

		if (!frm.doc.applies_to_doctype) {
			return;
		}

		let filters = [];
		if (frm.doc.filters_json && frm.doc.filters_json !== "[]") {
			filters = JSON.parse(frm.doc.filters_json);
		} else if (frm.doc.conditions && frm.doc.conditions.length > 0) {
			// Migration: Convert existing conditions to filters
			const op_map = {
				Equals: "=",
				"Not Equals": "!=",
				Like: "like",
				"Not Like": "not like",
				In: "in",
				"Not In": "not in",
				Is: "is",
			};

			filters = frm.doc.conditions.map((row) => {
				return [
					frm.doc.applies_to_doctype,
					row.conditional_field,
					op_map[row.condition] || "=",
					row.value,
				];
			});
		}

		frappe.model.with_doctype(frm.doc.applies_to_doctype, () => {
			const filter_group = new frappe.ui.FilterGroup({
				parent: parent,
				doctype: frm.doc.applies_to_doctype,
				on_change: () => {
					const current_filters = filter_group.get_filters();
					// Explicitly map to [doctype, field, operator, value] to remove any extra internal flags
					const clean_filters = current_filters.map((f) => [f[0], f[1], f[2], f[3]]);

					frm.set_value("filters_json", JSON.stringify(clean_filters));

					// Also sync back to conditions table for backward compatibility (optional, but good for safety)
					// We clear and rebuild the table
					frm.clear_table("conditions");
					const rev_op_map = {
						"=": "Equals",
						"!=": "Not Equals",
						like: "Like",
						"not like": "Not Like",
						in: "In",
						"not in": "Not In",
						is: "Is",
					};

					const value_for_condition_row = (filter_op, val) => {
						// Child table `value` is Data — must be a string (In/Not In use arrays in FilterGroup).
						if (Array.isArray(val)) {
							return val
								.map((v) => (v == null || v === undefined ? "" : String(v).trim()))
								.filter((s) => s !== "")
								.join(", ");
						}
						if (val === null || val === undefined) {
							return "";
						}
						return String(val);
					};

					current_filters.forEach((f) => {
						// f is [doctype, field, op, value]
						let row = frm.add_child("conditions");
						row.conditional_field = f[1];
						row.condition = rev_op_map[f[2]] || "Equals";
						row.value = value_for_condition_row(f[2], f[3]);
					});
					frm.refresh_field("conditions");
				},
			});

			filter_group.add_filters_to_filter_group(filters);
			console.log("Initialized filters:", filter_group);
			// UI Polish: Replace icons and fix styles
			const polish_ui = () => {
				// Replace 'X' with Delete Icon
				parent.find(".remove-filter").each(function () {
					const $btn = $(this);
					if (!$btn.find("svg").length) {
						$btn.html(frappe.utils.icon("delete", "sm"));
					}
				});

				// Ensure Add button style
				parent.find(".add-filter").addClass("btn btn-sm");
			};

			// Run initially
			setTimeout(polish_ui, 100);

			// Watch for new rows
			const observer = new MutationObserver((mutations) => {
				polish_ui();
			});

			observer.observe(parent[0], { childList: true, subtree: true });
		});
	},
});

// frappe.ui.form.on("Approval Matrix Item", {
    // approver_type: function (frm, cdt, cdn) {
    //     let row = locals[cdt][cdn];
    //     let grid = frm.fields_dict.approval_stages.grid;

    //     let grid_row = grid.grid_rows.find(r => r.doc.name === row.name);

    //     if (grid_row) {
    //         const approverFieldMap = {
    //             "Role": "role",
    //             "User": "employee",
    //             "Team": "team"
    //         };

    //         Object.values(approverFieldMap).forEach(field => {
    //             grid_row.toggle_reqd(field, false);
	// 			grid_row.set_field_property(field, "hidden", true);
    //             grid_row.refresh_field(field);
    //         });

    //         const requiredField = approverFieldMap[row.approver_type];
    //         if (requiredField) {
    //             grid_row.toggle_reqd(requiredField, true);
	// 			grid_row.set_field_property(requiredField, "hidden", false);
    //             grid_row.refresh_field(requiredField);
    //         }
    //     }
    // },

    // send_email: function (frm, cdt, cdn) {
    //     let row = locals[cdt][cdn];
    //     let grid = frm.fields_dict.approval_stages.grid;

    //     let grid_row = grid.grid_rows.find(r => r.doc.name === row.name);

    //     if (grid_row) {
    //         grid_row.toggle_reqd("email_template", row.send_email === 1);
    //         grid_row.refresh_field("email_template");
    //     }
    // },
// });
