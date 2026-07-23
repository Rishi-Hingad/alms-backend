frappe.ready(() => {

	const params = new URLSearchParams(window.location.search);

	const user = params.get("user");
	const company = params.get("company");
	const quotation = params.get("quotation_form");

	setTimeout(() => {

		if (user) frappe.web_form.set_value("user", user);
		if (company) frappe.web_form.set_value("company", company);
		if (quotation) frappe.web_form.set_value("quotation_form", quotation);

		["user", "company", "quotation_form"].forEach(field => {
			frappe.web_form.set_df_property(field, "read_only", 1);
		});

	}, 800);

});