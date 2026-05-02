frappe.ready(() => {

	const params = new URLSearchParams(window.location.search);

	const user = params.get("user");
	const company = params.get("company");
	const quotation = params.get("quotation_form");

	setTimeout(() => {

		if (company) frappe.web_form.set_value("vendor", company);
		if (quotation) frappe.web_form.set_value("employee_car_process_form", quotation);

		["vendor", "employee_car_process_form"].forEach(field => {
			frappe.web_form.set_df_property(field, "read_only", 1);
		});

	}, 800);

});