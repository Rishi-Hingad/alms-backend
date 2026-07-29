frappe.ui.form.on("Approval Matrix", {
	refresh(frm) {
		set_conditional_field_options(frm);
	},

	applies_to_doctype(frm) {
		(frm.doc.conditions || []).forEach((row) => {
			row.conditional_field = "";
		});
		frm.refresh_field("conditions");
		set_conditional_field_options(frm);
	},
});

frappe.ui.form.on("Approval Condition", {
	conditions_add(frm) {
		set_conditional_field_options(frm);
	},
	form_render(frm) {
		set_conditional_field_options(frm);
	},
});

function set_conditional_field_options(frm) {
	const grid = frm.fields_dict.conditions && frm.fields_dict.conditions.grid;
	if (!grid) return;

	if (!frm.doc.applies_to_doctype) {
		grid.update_docfield_property("conditional_field", "options", [""]);
		return;
	}

	frappe.model.with_doctype(frm.doc.applies_to_doctype, () => {
		const skip_types = [
			"Section Break",
			"Column Break",
			"Tab Break",
			"HTML",
			"Button",
			"Table",
			"Table MultiSelect",
		];
		const fieldnames = (frappe.get_meta(frm.doc.applies_to_doctype).fields || [])
			.filter((df) => df.fieldname && !skip_types.includes(df.fieldtype))
			.map((df) => df.fieldname);

		console.log(
			"[approval_matrix] populating Conditional Field for",
			frm.doc.applies_to_doctype,
			"->",
			fieldnames.length,
			"fields"
		);

		grid.update_docfield_property(
			"conditional_field",
			"options",
			[""].concat(fieldnames)
		);
	});
}
