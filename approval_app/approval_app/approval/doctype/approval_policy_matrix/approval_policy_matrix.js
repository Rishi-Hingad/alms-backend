// Copyright (c) 2025, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Approval Policy Matrix", {
	setup: function (frm) {
		frm.fields_dict["approval_stages"].grid.get_field("form_for_approval").get_query =
			function (doc, cdt, cdn) {
				return {
					filters: {
						doc_type: frm.doc.target_doctype,
					},
				};
			};
		frm.fields_dict["approval_stages"].grid.get_field("form_for_rejection").get_query =
			function (doc, cdt, cdn) {
				return {
					filters: {
						doc_type: frm.doc.target_doctype,
					},
				};
			};
		add_options_in_user_field(frm);
		add_options_employee_user_link_field(frm);
		add_options_in_update_field(frm);
		add_escalation_employee_field(frm);
		add_options_in_cc_employee_field(frm);
	},
	refresh(frm) {
		add_options_in_user_field(frm);
		add_options_in_update_field(frm);
		add_options_in_cc_employee_field(frm);
		add_options_employee_user_link_field(frm);
		add_escalation_employee_field(frm);
		fetchEmployeeLinkFields(frm);
		render_filter_ui(frm);
	},
	select_employee_field: (frm) => {
		if (frm.doc.select_employee_field) {
			let parent_field = frm.doc.select_employee_field.split(" (Parent field: ")[1];
			parent_field = parent_field ? parent_field.replace(")", "") : "";
			frm.set_value("parent_employee_link_field", parent_field);
		}
	},
	target_doctype(frm) {
		add_options_in_user_field(frm);
		fetchEmployeeLinkFields(frm);
		add_options_employee_user_link_field(frm);
		add_escalation_employee_field(frm);
		render_filter_ui(frm);
	},
});

async function add_options_employee_user_link_field(frm) {
	await frappe.model.with_doctype("Employee");
	const meta = frappe.get_meta("Employee");

	const allowed_fields = (meta.fields || [])
		.filter((df) => df.fieldtype === "Link" && ["User", "Employee"].includes(df.options))
		.map((df) => df.fieldname)
		.filter(Boolean);

	// unique + sorted
	const uniqueSorted = Array.from(new Set(allowed_fields)).sort();
	frm.fields_dict["approval_stages"].grid.update_docfield_property(
		"employee_doc_field",
		"options",
		[""].concat(uniqueSorted)
	);
	frm.refresh_field("employee_doc_field");
}

async function add_escalation_employee_field(frm) {
	await frappe.model.with_doctype("Employee");
	const meta = frappe.get_meta("Employee");

	const allowed_fields = (meta.fields || [])
		.filter((df) => df.fieldtype === "Link" && ["User", "Employee"].includes(df.options))
		.map((df) => df.fieldname)
		.filter(Boolean);

	// unique + sorted
	const uniqueSorted = Array.from(new Set(allowed_fields)).sort();
	frm.fields_dict["approval_stages"].grid.update_docfield_property(
		"escalation_employee_field",
		"options",
		[""].concat(uniqueSorted)
	);
	frm.refresh_field("escalation_employee_field");
}

async function add_options_in_cc_employee_field(frm) {
	if (!frm.fields_dict["approval_stages"]) return;
	await frappe.model.with_doctype("Employee");
	const meta = frappe.get_meta("Employee");
	const allowed_fields = meta.fields
		.filter((df) => df.fieldtype === "Link" && df.options === "User")
		.map((df) => df.fieldname)
		.filter((v, i, a) => a.indexOf(v) === i)
		.sort();
	frm.fields_dict["approval_stages"].grid.update_docfield_property(
		"cc_employee_field",
		"options",
		[""].concat(allowed_fields)
	);

	frm.refresh_field("approval_stages");
}

function add_options_in_update_field(frm) {
	if (frm.doc.target_doctype) {
		frappe.model.with_doctype(frm.doc.target_doctype, () => {
			const meta = frappe.get_meta(frm.doc.target_doctype);
			const system_fields = [
				"name",
				"owner",
				"creation",
				"modified",
				"modified_by",
				"docstatus",
				"idx",
				"parent",
				"parenttype",
				"parentfield",
			];

			const allowed_fields = meta.fields
				.filter(
					(field) =>
						field.fieldtype !== "Table" &&
						field.fieldtype !== "Tab Break" &&
						field.fieldtype !== "Column Break" &&
						field.fieldtype !== "Section Break" &&
						!system_fields.includes(field.fieldname)
				)
				.map((field) => field.fieldname);

			frm.fields_dict["approval_stages"].grid.update_docfield_property(
				"update_field",
				"options",
				[""].concat(allowed_fields)
			);
			frm.fields_dict["approval_stages"].grid.update_docfield_property(
				"field_to_update_on_rejection",
				"options",
				[""].concat(allowed_fields)
			);
		});
	}
}

function add_options_in_user_field(frm) {
	if (frm.doc.target_doctype) {
		frappe.model.with_doctype(frm.doc.target_doctype, () => {
			const meta = frappe.get_meta(frm.doc.target_doctype);
			var employee_link_fields = [];

			// Collect Employee link fields
			meta.fields.forEach((field) => {
				if (field.fieldtype === "Link" && field.options === "User") {
					employee_link_fields.push(field.fieldname);
				}
			});
			// Use update_docfield_property to set the options for the 'user_field' in the child table
			frm.fields_dict["approval_stages"].grid.update_docfield_property(
				"user_field",
				"options",
				[""].concat(employee_link_fields)
			);
		});
	}
}

frappe.ui.form.on("Approval Stages", {
	user_field: (frm, cdt, cdn) => {
		add_options_in_user_field(frm);
	},
	update_field: (frm, cdt, cdn) => {
		add_options_in_update_field(frm);
	},
	field_to_update_on_rejection: (frm, cdt, cdn) => {
		add_options_in_update_field(frm);
	},
	approval_stages_add: (frm, cdt, cdn) => {
		add_options_in_user_field(frm);
		add_options_in_update_field(frm);
		add_options_in_cc_employee_field(frm);
		add_options_employee_user_link_field(frm);
		add_escalation_employee_field(frm);
	},
	cc_based_on: (frm, cdt, cdn) => {
		if (frm.doc.cc_based_on === "Employee Field") {
			add_options_in_cc_employee_field(frm);
		}
	},
	escalation_based_on: (frm, cdt, cdn) => {
		if (frm.doc.escalation_based_on === "Employee Field") {
			add_escalation_employee_field(frm);
		}
	},
});

function fetchEmployeeLinkFields(frm) {
	if (!frm.doc.target_doctype) return;

	frappe.model.with_doctype(frm.doc.target_doctype, () => {
		const meta = frappe.get_meta(frm.doc.target_doctype);
		const employee_link_fields = new Set();
		const promises = [];

		meta.fields.forEach((field) => {
			if (field.fieldtype === "Link" && field.options) {
				const parent_field_label =
					field.fieldname === "amended_from" ? "doc" : field.fieldname;

				if (field.options === "Employee") {
					employee_link_fields.add(`name (Parent field: doc)`);
				}

				const nested_promise = new Promise((resolve) => {
					frappe.model.with_doctype(field.options, () => {
						const nested_meta = frappe.get_meta(field.options);
						nested_meta.fields.forEach((nested_field) => {
							if (
								nested_field.fieldtype === "Link" &&
								nested_field.options === "Employee"
							) {
								employee_link_fields.add(
									`${nested_field.fieldname} (Parent field: ${parent_field_label})`
								);
							}
						});
						resolve();
					});
				});

				promises.push(nested_promise);
			}
		});

		Promise.all(promises).then(() => {
			if (employee_link_fields.size > 0) {
				frm.set_df_property(
					"select_employee_field",
					"options",
					Array.from(employee_link_fields).join("\n")
				);
			}
		});
	});
}

var $ = jQuery;
function render_filter_ui(frm) {
	const wrapper = frm.fields_dict["approval_condtions"].$wrapper;
	wrapper.empty(); // Clear existing content

	// Define the operators configuration - this remains static
	const filterConfig = {
		targetTypes: [], // Will be populated dynamically
		fields: {}, // Will be populated dynamically
		operators: {
			Data: [
				{ label: "Equals", value: "=" },
				{ label: "Not Equals", value: "!=" },
				{ label: "Like", value: "like" },
				{ label: "Not Like", value: "not like" },
				{ label: "In", value: "in" },
			],
			Link: [
				{ label: "Equals", value: "=" },
				{ label: "Not Equals", value: "!=" },
				{ label: "In", value: "in" },
			],
			Currency: [
				{ label: "Equals", value: "=" },
				{ label: "Not Equals", value: "!=" },
				{ label: "Greater Than", value: ">" },
				{ label: "Less Than", value: "<" },
				{ label: "Greater Than or Equal To", value: ">=" },
				{ label: "Less Than or Equal To", value: "<=" },
				{ label: "Between", value: "between" },
			],
			Int: [
				{ label: "Equals", value: "=" },
				{ label: "Not Equals", value: "!=" },
				{ label: "Greater Than", value: ">" },
				{ label: "Less Than", value: "<" },
				{ label: "Greater Than or Equal To", value: ">=" },
				{ label: "Less Than or Equal To", value: "<=" },
				{ label: "Between", value: "between" },
			],
			Float: [
				{ label: "Equals", value: "=" },
				{ label: "Not Equals", value: "!=" },
				{ label: "Greater Than", value: ">" },
				{ label: "Less Than", value: "<" },
				{ label: "Greater Than or Equal To", value: ">=" },
				{ label: "Less Than or Equal To", value: "<=" },
				{ label: "Between", value: "between" },
			],
			Check: [{ label: "Equals", value: "=" }],
			Date: [
				{ label: "Equals", value: "=" },
				{ label: "Not Equals", value: "!=" },
				{ label: "Before", value: "<" },
				{ label: "After", value: ">" },
				{ label: "Between", value: "between" },
			],
			Datetime: [
				{ label: "Equals", value: "=" },
				{ label: "Not Equals", value: "!=" },
				{ label: "Before", value: "<" },
				{ label: "After", value: ">" },
				{ label: "Between", value: "between" },
			],
			Select: [
				{ label: "Equals", value: "=" },
				{ label: "Not Equals", value: "!=" },
				{ label: "In", value: "in" },
			],
		},
	};

	// Add filter builder container with styling
	wrapper.append(`
        <div id="filter-builder" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; width: 100%; background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); padding: 16px; margin: 20px 0;">
            <div id="filters-container">
                <!-- Filter rows will be added here -->
            </div>

            <div style="display: flex; justify-content: space-between; margin-top: 16px;">
                <button id="add-filter-btn" style="background: none; border: none; color: #4F46E5; font-size: 14px; cursor: pointer; display: flex; align-items: center; padding: 8px 0;">
                    <span style="margin-right: 4px; font-weight: bold;">+</span> Add a Condition
                </button>
                <div>
                    <button id="clear-filters-btn" style="background: none; border: 1px solid #E5E7EB; color: #374151; font-size: 14px; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 8px;">
                        Clear Conditions
                    </button>
                    <button id="apply-filters-btn" style="background-color: #111827; border: none; color: white; font-size: 14px; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        Apply Conditions
                    </button>
                </div>
            </div>
        </div>
    `);

	const filtersContainer = wrapper.find("#filters-container");
	const addFilterBtn = wrapper.find("#add-filter-btn");
	const clearFiltersBtn = wrapper.find("#clear-filters-btn");
	const applyFiltersBtn = wrapper.find("#apply-filters-btn");

	let filterIndex = 0;

	// Function to create a styled select element
	function createStyledSelect(className, width) {
		return `<select class="${className}" style="padding: 8px 12px; border-radius: 4px; border: none; background-color: #F3F4F6; width: ${
			width || "150px"
		}; font-size: 14px; color: #374151; appearance: none; background-image: url('data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'12\\' height=\\'12\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'%23374151\\' stroke-width=\\'2\\' stroke-linecap=\\'round\\' stroke-linejoin=\\'round\\'%3E%3Cpolyline points=\\'6 9 12 15 18 9\\'%3E%3C/polyline%3E%3C/svg%3E'); background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px;"></select>`;
	}

	// Function to create a styled input element
	function createStyledInput(type, className, placeholder) {
		return `<input type="${type}" class="${className}" ${
			placeholder ? `placeholder="${placeholder}"` : ""
		} style="padding: 8px 12px; border-radius: 4px; border: none; background-color: #F3F4F6; width: 100%; font-size: 14px; color: #374151; box-sizing: border-box;">`;
	}

	// Function to create a styled textarea element
	function createStyledTextarea(className, placeholder) {
		return `<textarea class="${className}" ${
			placeholder ? `placeholder="${placeholder}"` : ""
		} style="padding: 8px 12px; border-radius: 4px; border: none; background-color: #F3F4F6; width: 100%; font-size: 14px; color: #374151; box-sizing: border-box; min-height: 60px; resize: vertical;"></textarea>`;
	}

	// Function to add a new filter row
	function addFilterRow() {
		const rowHtml = `
            <div class="filter-row" data-index="${filterIndex++}" style="display: flex; align-items: center; margin-bottom: 12px; gap: 8px;">
                ${createStyledSelect("target-type-select", "150px")}
                ${createStyledSelect("field-select", "150px")}
                ${createStyledSelect("operator-select", "150px")}
                <div class="value-container" style="flex: 1;"></div>
                ${createStyledSelect("join-type-select", "100px")}
                <button class="remove-filter-btn" style="background: none; border: none; color: #9CA3AF; font-size: 18px; cursor: pointer; padding: 4px 8px; display: flex; align-items: center; justify-content: center;">&times;</button>
            </div>
        `;

		filtersContainer.append(rowHtml);

		const newRow = filtersContainer.find(`.filter-row[data-index="${filterIndex - 1}"]`);
		const targetTypeSelect = newRow.find(".target-type-select");
		const fieldSelect = newRow.find(".field-select");
		const operatorSelect = newRow.find(".operator-select");
		const valueContainer = newRow.find(".value-container");
		const joinTypeSelect = newRow.find(".join-type-select");

		// Populate Join Type options
		joinTypeSelect.append('<option value="">Join...</option>');
		joinTypeSelect.append('<option value="AND">AND</option>');
		joinTypeSelect.append('<option value="OR">OR</option>');
		joinTypeSelect.val("AND"); // Default

		// Populate target type options
		let targetTypeOptions = "";
		filterConfig.targetTypes.forEach((targetType) => {
			targetTypeOptions += `<option value="${targetType.value}">${targetType.label}</option>`;
		});
		targetTypeSelect.html(targetTypeOptions);

		// Set up event handlers for cascading updates
		targetTypeSelect.on("change", function () {
			updateFieldOptions($(this), fieldSelect);
			// Clear operator and value when target type changes
			operatorSelect.empty();
			valueContainer.empty();
		});

		fieldSelect.on("change", function () {
			updateOperatorOptions($(this), operatorSelect);
			updateValueInput($(this), operatorSelect, valueContainer);
		});

		operatorSelect.on("change", function () {
			updateValueInput(fieldSelect, $(this), valueContainer);
		});

		// Initialize the cascading dropdowns if we have target types
		if (filterConfig.targetTypes.length > 0) {
			updateFieldOptions(targetTypeSelect, fieldSelect);
		}

		// Set up remove button
		newRow.find(".remove-filter-btn").on("click", function () {
			$(this).closest(".filter-row").remove();
		});
	}

	function isDuplicateFilter(targetType, fieldName, operator, value) {
		let isDuplicate = false;

		filtersContainer.find(".filter-row").each(function () {
			const row = $(this);
			const existingTargetType = row.find(".target-type-select").val();
			const existingFieldName = row.find(".field-select").val();
			const existingOperator = row.find(".operator-select").val();

			// Get existing value based on input type
			let existingValue;
			const valueInput = row.find(".value-input");
			const valueInputMin = row.find(".value-input-min");
			const valueInputMax = row.find(".value-input-max");

			if (valueInputMin.length && valueInputMax.length) {
				existingValue = {
					min: valueInputMin.val(),
					max: valueInputMax.val(),
				};
			} else if (valueInput.length) {
				existingValue = valueInput.val();
			}

			// Compare all components to check for duplicates
			if (
				existingTargetType === targetType &&
				existingFieldName === fieldName &&
				existingOperator === operator
			) {
				// For between operator with min/max values
				if (typeof value === "object" && typeof existingValue === "object") {
					if (value.min === existingValue.min && value.max === existingValue.max) {
						isDuplicate = true;
						return false; // Break the each loop
					}
				}
				// For simple values
				else if (value === existingValue) {
					isDuplicate = true;
					return false; // Break the each loop
				}
			}
		});

		return isDuplicate;
	}

	// Function to update field options based on selected target type
	function updateFieldOptions(targetTypeSelect, fieldSelect) {
		const targetType = targetTypeSelect.val();

		// Clear existing options
		fieldSelect.empty();

		// If we already have the fields for this target type, use them
		if (filterConfig.fields[targetType]) {
			populateFieldOptions(targetType, fieldSelect);
			return;
		}

		// Otherwise, fetch the fields dynamically
		const doctypeToFetch =
			targetType === "doc"
				? frm.doc.target_doctype
				: frappe
						.get_meta(frm.doc.target_doctype)
						.fields.find((f) => f.fieldname === targetType)?.options;

		if (!doctypeToFetch) return;

		// Show loading indicator
		fieldSelect.html('<option value="">Loading fields...</option>');

		frappe.model.with_doctype(doctypeToFetch, () => {
			const meta = frappe.get_meta(doctypeToFetch);
			filterConfig.fields[targetType] = meta.fields;
			populateFieldOptions(targetType, fieldSelect);
		});
	}

	// Helper function to populate field options
	function populateFieldOptions(targetType, fieldSelect) {
		fieldSelect.empty();

		filterConfig.fields[targetType].forEach((field) => {
			// Skip hidden and section break fields
			if (
				field.hidden ||
				field.fieldtype === "Section Break" ||
				field.fieldtype === "Column Break" ||
				field.fieldtype === "HTML" ||
				field.fieldtype === "Button" ||
				field.fieldtype === "Table"
			) {
				return;
			}

			const option = $(
				`<option value="${field.fieldname}" data-type="${field.fieldtype}">${
					field.label || field.fieldname
				}</option>`
			);

			if (field.fieldtype === "Select" && field.options) {
				// For Select fields, store the options
				const options = field.options.split("\n").filter((opt) => opt.trim());
				option.attr("data-options", JSON.stringify(options));
			}

			fieldSelect.append(option);
		});

		// Trigger change event to update operators
		if (fieldSelect.find("option").length > 0) {
			fieldSelect.trigger("change");
		}
	}

	// Function to update operator options based on selected field
	function updateOperatorOptions(fieldSelect, operatorSelect) {
		const selectedOption = fieldSelect.find("option:selected");
		const fieldType = selectedOption.data("type");

		// Clear existing options
		operatorSelect.empty();

		// Map Frappe field types to our operator types
		let operatorType = fieldType;
		if (["Small Text", "Text", "Text Editor", "Code", "Data"].includes(fieldType)) {
			operatorType = "Data";
		} else if (["Percent", "Currency", "Float", "Decimal"].includes(fieldType)) {
			operatorType = "Float";
		} else if (["Int", "Integer"].includes(fieldType)) {
			operatorType = "Int";
		}

		// Add new options based on field type
		if (filterConfig.operators[operatorType]) {
			filterConfig.operators[operatorType].forEach((operator) => {
				operatorSelect.append(
					`<option value="${operator.value}">${operator.label}</option>`
				);
			});

			// Trigger change event to update value input
			operatorSelect.trigger("change");
		} else {
			// Default to Data operators if we don't have specific ones
			filterConfig.operators.Data.forEach((operator) => {
				operatorSelect.append(
					`<option value="${operator.value}">${operator.label}</option>`
				);
			});
			operatorSelect.trigger("change");
		}
	}

	// Function to update the value input based on the selected field and operator
	function updateValueInput(fieldSelect, operatorSelect, valueContainer) {
		if (fieldSelect.find("option").length === 0 || operatorSelect.find("option").length === 0)
			return;

		const selectedFieldOption = fieldSelect.find("option:selected");
		const fieldType = selectedFieldOption.data("type");
		const fieldName = selectedFieldOption.val();
		const targetType = fieldSelect.closest(".filter-row").find(".target-type-select").val();
		const operatorValue = operatorSelect.val();

		// Clear the value container
		valueContainer.empty();

		// Create the appropriate input based on field type and operator
		if (fieldType === "Check") {
			// Create a Yes/No dropdown for Check fields
			const selectHtml = createStyledSelect("value-input", "100%");
			valueContainer.html(selectHtml);

			const select = valueContainer.find(".value-input");
			select.append('<option value="1">Yes</option>');
			select.append('<option value="0">No</option>');
		} else if (fieldType === "Select") {
			// Create a dropdown for Select fields with options fetched from metadata
			const selectHtml = createStyledSelect("value-input", "100%");
			valueContainer.html(selectHtml);

			const select = valueContainer.find(".value-input");
			select.html('<option value="">Loading options...</option>');

			// Get the doctype based on target type
			const doctypeToFetch =
				targetType === "doc"
					? frm.doc.target_doctype
					: frappe
							.get_meta(frm.doc.target_doctype)
							.fields.find((f) => f.fieldname === targetType)?.options;

			if (doctypeToFetch) {
				// Fetch options from the field's metadata
				frappe.model.with_doctype(doctypeToFetch, () => {
					const options = frappe.meta.get_docfield(doctypeToFetch, fieldName)?.options;
					if (options) {
						const optionsList = options.split("\n").filter((opt) => opt.trim());
						select.empty();
						optionsList.forEach((optionText) => {
							select.append(`<option value="${optionText}">${optionText}</option>`);
						});
					}
				});
			}
		} else if (fieldType === "Link") {
			// For Link fields, create an autocomplete input
			valueContainer.html(createStyledInput("text", "value-input"));
			const input = valueContainer.find(".value-input");

			// Get the linked doctype
			const doctypeToFetch =
				targetType === "doc"
					? frm.doc.target_doctype
					: frappe
							.get_meta(frm.doc.target_doctype)
							.fields.find((f) => f.fieldname === targetType)?.options;

			if (doctypeToFetch) {
				const linkDoctype = frappe.meta.get_docfield(doctypeToFetch, fieldName)?.options;

				if (linkDoctype) {
					// Set up autocomplete for link field
					input.attr("data-link-doctype", linkDoctype);

					// Initialize the autocomplete
					input.on("input", function () {
						const searchText = $(this).val();

						// Use the recommended Frappe method to fetch link options
						frappe.db
							.get_link_options(linkDoctype, searchText)
							.then((results) => {
								// Create a datalist for autocomplete suggestions
								const datalistId = `link-options-${fieldName}`;

								// Remove existing datalist if any
								$(`#${datalistId}`).remove();

								// Create new datalist
								const datalist = $(`<datalist id="${datalistId}"></datalist>`);

								// Add options to datalist
								results.forEach((result) => {
									datalist.append(
										`<option value="${result.value}">${
											result.description || ""
										}</option>`
									);
								});

								// Append datalist to document
								$("body").append(datalist);

								// Connect input to datalist
								input.attr("list", datalistId);
							})
							.catch((err) => {
								console.error("Error fetching link options:", err);
							});
					});

					// Trigger initial load of options
					setTimeout(() => {
						input.trigger("input");
					}, 100);
				}
			}
		} else if (["Currency", "Float", "Int", "Decimal", "Percent"].includes(fieldType)) {
			// For numeric fields, create a toggle between static value and field reference

			// First, create the toggle container
			valueContainer.html(`
        <div style="display: flex; flex-direction: column; width: 100%;">
          <div style="display: flex; margin-bottom: 8px;">
            <label style="display: flex; align-items: center; margin-right: 16px; cursor: pointer;">
              <input type="radio" name="value-type-${
					filterIndex - 1
				}" class="value-type-radio" value="static" checked style="margin-right: 4px;">
              <span>Static Value</span>
            </label>
            <label style="display: flex; align-items: center; cursor: pointer;">
              <input type="radio" name="value-type-${
					filterIndex - 1
				}" class="value-type-radio" value="field" style="margin-right: 4px;">
              <span>Field Reference</span>
            </label>
          </div>
          <div class="value-input-container" style="width: 100%;"></div>
        </div>
      `);

			const valueInputContainer = valueContainer.find(".value-input-container");
			const valueTypeRadios = valueContainer.find(".value-type-radio");

			// Function to update the input type based on the selected radio
			function updateInputType() {
				const selectedType = valueContainer.find(".value-type-radio:checked").val();
				valueInputContainer.empty();

				if (selectedType === "static") {
					// Show static value input(s)
					if (operatorValue === "between") {
						// For 'between' operator, create two inputs
						valueInputContainer.html(`
              <div style="display: flex; gap: 8px;">
                ${createStyledInput("number", "value-input-min", "Min")}
                ${createStyledInput("number", "value-input-max", "Max")}
              </div>
            `);

						// Add step attribute for Float/Currency fields
						if (["Currency", "Float", "Decimal", "Percent"].includes(fieldType)) {
							valueInputContainer.find("input").attr("step", "0.01");
						}
					} else {
						// For other operators, create a single input
						valueInputContainer.html(createStyledInput("number", "value-input"));

						// Add step attribute for Float/Currency fields
						if (["Currency", "Float", "Decimal", "Percent"].includes(fieldType)) {
							valueInputContainer.find("input").attr("step", "0.01");
						}
					}
				} else {
					// Show field reference dropdown
					// Get the current field's operator type (Float or Int)
					const operatorType = ["Percent", "Currency", "Float", "Decimal"].includes(
						fieldType
					)
						? "Float"
						: "Int";

					// Create a dropdown for selecting fields of the same type
					valueInputContainer.html(
						createStyledSelect("value-input field-reference", "100%")
					);
					const fieldReferenceSelect = valueInputContainer.find(".field-reference");
					fieldReferenceSelect.html('<option value="">Select a field...</option>');

					// Get the doctype based on target type
					const doctypeToFetch =
						targetType === "doc"
							? frm.doc.target_doctype
							: frappe
									.get_meta(frm.doc.target_doctype)
									.fields.find((f) => f.fieldname === targetType)?.options;

					if (doctypeToFetch) {
						// Fetch fields of the same type
						frappe.model.with_doctype(doctypeToFetch, () => {
							const meta = frappe.get_meta(doctypeToFetch);
							const fields = meta.fields.filter((f) => {
								// Match fields with the same operator type (Float or Int)
								if (operatorType === "Float") {
									return ["Percent", "Currency", "Float", "Decimal"].includes(
										f.fieldtype
									);
								} else if (operatorType === "Int") {
									return ["Int", "Integer"].includes(f.fieldtype);
								}
								return false;
							});

							// Add options to the dropdown
							fields.forEach((field) => {
								// Skip the current field (can't compare with itself)
								if (field.fieldname !== fieldName) {
									fieldReferenceSelect.append(
										`<option value="${field.fieldname}" data-fieldtype="${
											field.fieldtype
										}">${field.label || field.fieldname}</option>`
									);
								}
							});

							// If no matching fields found
							if (fields.length <= 1) {
								fieldReferenceSelect.html(
									'<option value="">No matching fields available</option>'
								);
							}
						});
					}
				}
			}

			// Set up event handlers for the radio buttons
			valueTypeRadios.on("change", updateInputType);

			// Initialize with static value input
			updateInputType();
		} else if (["Date", "Datetime"].includes(fieldType)) {
			// Create date input(s) for Date fields
			if (operatorValue === "between") {
				// For 'between' operator, create two inputs
				valueContainer.html(`
                    <div style="display: flex; gap: 8px;">
                        ${createStyledInput(fieldType.toLowerCase(), "value-input-min")}
                        ${createStyledInput(fieldType.toLowerCase(), "value-input-max")}
                    </div>
                `);
			} else {
				// For other operators, create a single input
				valueContainer.html(createStyledInput(fieldType.toLowerCase(), "value-input"));
			}
		} else {
			// Create a text input for all other fields
			if (operatorValue === "in") {
				// For 'in' operator, create a textarea for comma-separated values
				valueContainer.html(
					createStyledTextarea("value-input", "Enter comma-separated values")
				);
			} else {
				// For other operators, create a single input
				valueContainer.html(createStyledInput("text", "value-input"));
			}
		}
	}

	// Function to clear all filters
	function clearFilters() {
		filtersContainer.empty();
		filterIndex = 0;
		addFilterRow();
	}

	// Function to apply filters
	function applyFilters() {
		const filters = [];
		const duplicates = [];

		filtersContainer.find(".filter-row").each(function () {
			const row = $(this);
			const targetTypeSelect = row.find(".target-type-select");
			const fieldSelect = row.find(".field-select");
			const operatorSelect = row.find(".operator-select");
			const joinTypeSelect = row.find(".join-type-select");

			// Handle different value input types
			let value = null;
			let isFieldReference = false;

			// Check if this is a numeric field with field reference
			const fieldType = fieldSelect.find("option:selected").data("type");
			const isNumericField = ["Currency", "Float", "Int", "Decimal", "Percent"].includes(
				fieldType
			);

			if (isNumericField && row.find(".value-type-radio:checked").val() === "field") {
				// This is a field reference
				const fieldReferenceSelect = row.find(".field-reference");
				value = fieldReferenceSelect.val();
				isFieldReference = true;
			} else {
				// Standard value handling
				const valueInput = row.find(".value-input");
				const valueInputMin = row.find(".value-input-min");
				const valueInputMax = row.find(".value-input-max");

				if (valueInputMin.length && valueInputMax.length) {
					// For 'between' operator
					value = {
						min: valueInputMin.val(),
						max: valueInputMax.val(),
					};
				} else if (valueInput.length) {
					value = valueInput.val();
				}
			}

			// Only add filter if all fields are selected and value is provided
			if (targetTypeSelect.val() && fieldSelect.val() && operatorSelect.val() && value) {
				const targetTypeOption = targetTypeSelect.find("option:selected");
				const fieldOption = fieldSelect.find("option:selected");
				const operatorOption = operatorSelect.find("option:selected");

				// Check for duplicates in the current set of filters
				const filterData = {
					target_type: targetTypeSelect.val(),
					target_type_label: targetTypeOption.text(),
					field: fieldSelect.val(),
					field_label: fieldOption.text(),
					operator: operatorSelect.val(),
					operator_label: operatorOption.text(),
					value: value,
					field_type: fieldOption.data("type"),
					join_type: joinTypeSelect.val(),
					is_field_reference: isFieldReference,
				};

				// Check if this filter is a duplicate
				let isDuplicate = false;
				for (let i = 0; i < filters.length; i++) {
					const existingFilter = filters[i];

					if (
						existingFilter.target_type === filterData.target_type &&
						existingFilter.field === filterData.field &&
						existingFilter.operator === filterData.operator
					) {
						// For between operator with min/max values
						if (
							typeof filterData.value === "object" &&
							typeof existingFilter.value === "object"
						) {
							if (
								filterData.value.min === existingFilter.value.min &&
								filterData.value.max === existingFilter.value.max
							) {
								isDuplicate = true;
								break;
							}
						}
						// For simple values
						else if (
							JSON.stringify(filterData.value) ===
							JSON.stringify(existingFilter.value)
						) {
							isDuplicate = true;
							break;
						}
					}
				}

				if (isDuplicate) {
					duplicates.push(filterData);
				} else {
					filters.push(filterData);
				}
			}
		});

		// Notify about duplicates if any
		if (duplicates.length > 0) {
			frappe.msgprint(`${duplicates.length} duplicate filter(s) were ignored.`);
		}

		// Add to child table in Frappe
		frm.doc.approval_rule_condition = [];

		filters.forEach((filter) => {
			const child = frappe.model.add_child(
				frm.doc,
				"Approval Rule Condition",
				"approval_rule_condition"
			);
			child.target_type = filter.target_type;
			child.field_name = filter.field;
			child.operator = filter.operator;
			child.join_type = filter.join_type;

			// Handle different value formats
			if (typeof filter.value === "object" && filter.value !== null) {
				// For 'between' operator
				child.value = `${filter.value.min}:${filter.value.max}`;
			} else {
				// For regular values or field references
				if (filter.is_field_reference) {
					// Prefix field references with 'field:' to distinguish them from static values
					child.value = `field:${filter.value}`;
				} else {
					child.value = filter.value;
				}
			}
		});

		frm.refresh_field("approval_rule_condition");
		frappe.msgprint(`${filters.length} filter(s) applied successfully`);
	}

	// Get dynamic target types then load UI
	set_target_type_options(frm, (targetTypes) => {
		filterConfig.targetTypes = targetTypes;

		// Set up event handlers
		addFilterBtn.on("click", () => {
			// Check if there are any incomplete rows before adding a new one
			let hasIncompleteRow = false;

			filtersContainer.find(".filter-row").each(function () {
				const row = $(this);
				const targetTypeSelect = row.find(".target-type-select");
				const fieldSelect = row.find(".field-select");
				const operatorSelect = row.find(".operator-select");

				// Get value based on input type
				let hasValue = false;

				// Check if this is a numeric field with field reference
				const fieldType = fieldSelect.find("option:selected").data("type");
				const isNumericField = ["Currency", "Float", "Int", "Decimal", "Percent"].includes(
					fieldType
				);

				if (isNumericField && row.find(".value-type-radio:checked").val() === "field") {
					// This is a field reference
					const fieldReferenceSelect = row.find(".field-reference");
					hasValue = !!fieldReferenceSelect.val();
				} else {
					// Standard value handling
					const valueInput = row.find(".value-input");
					const valueInputMin = row.find(".value-input-min");
					const valueInputMax = row.find(".value-input-max");

					if (valueInputMin.length && valueInputMax.length) {
						hasValue = valueInputMin.val() && valueInputMax.val();
					} else if (valueInput.length) {
						hasValue = !!valueInput.val();
					}
				}

				if (
					!targetTypeSelect.val() ||
					!fieldSelect.val() ||
					!operatorSelect.val() ||
					!hasValue
				) {
					hasIncompleteRow = true;
					return false; // Break the each loop
				}
			});

			if (hasIncompleteRow) {
				frappe.msgprint(
					"Please complete the existing filter row before adding a new one."
				);
			} else {
				addFilterRow();
			}
		});
		clearFiltersBtn.on("click", clearFilters);
		applyFiltersBtn.on("click", applyFilters);

		// Load saved filters if available
		if (frm.doc.approval_rule_condition && frm.doc.approval_rule_condition.length > 0) {
			frm.doc.approval_rule_condition.forEach((condition) => {
				addFilterRow();
				const lastIndex = filterIndex - 1;
				const row = filtersContainer.find(`.filter-row[data-index="${lastIndex}"]`);

				const targetTypeSelect = row.find(".target-type-select");
				const fieldSelect = row.find(".field-select");
				const operatorSelect = row.find(".operator-select");
				const valueContainer = row.find(".value-container");
				const joinTypeSelect = row.find(".join-type-select");

				// Restore Join Type
				if (condition.join_type) {
					joinTypeSelect.val(condition.join_type);
				}

				setTimeout(() => {
					targetTypeSelect.val(condition.target_type).trigger("change");

					setTimeout(() => {
						fieldSelect.val(condition.field_name).trigger("change");

						setTimeout(() => {
							operatorSelect.val(condition.operator).trigger("change");

							setTimeout(() => {
								// Check if this is a field reference (prefixed with 'field:')
								if (condition.value && condition.value.startsWith("field:")) {
									// This is a field reference
									const fieldName = condition.value.substring(6); // Remove 'field:' prefix

									// Select the "Field Reference" radio button
									row.find(".value-type-radio[value='field']")
										.prop("checked", true)
										.trigger("change");

									// Wait for the dropdown to be populated
									setTimeout(() => {
										row.find(".field-reference").val(fieldName);
									}, 100);
								} else if (
									condition.operator === "between" &&
									condition.value.includes(":")
								) {
									const [min, max] = condition.value.split(":");
									row.find(".value-input-min").val(min);
									row.find(".value-input-max").val(max);
								} else {
									row.find(".value-input").val(condition.value);
								}
							}, 100);
						}, 100);
					}, 100);
				}, 100);
			});
		} else {
			// If no saved filters, show a blank one
			addFilterRow();
		}
	});
}

// Function to dynamically get target type options
function set_target_type_options(frm, callback) {
	const doctype = frm.doc.target_doctype;
	if (!doctype) {
		callback([]);
		return;
	}

	frappe.model.with_doctype(doctype, () => {
		const meta = frappe.get_meta(doctype);
		const linkFields = meta.fields.filter((df) => df.fieldtype === "Link");
		const options = [
			{ label: doctype, value: "doc" },
			...linkFields.map((f) => ({ label: f.label || f.fieldname, value: f.fieldname })),
		];
		callback(options);
	});
}
