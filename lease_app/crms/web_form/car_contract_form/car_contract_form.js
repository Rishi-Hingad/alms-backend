frappe.ready(() => {

	const params = new URLSearchParams(window.location.search);

	const user = params.get("user");
	const company = params.get("company");
	const quotation = params.get("quotation_form");

	setTimeout(() => {

		if (company && company !== 'ALD') {
			frappe.web_form.set_value("vendor", company);
		}
		if (user) frappe.web_form.set_value("employee_car_process_form", user);
		if (quotation) frappe.web_form.set_value("quotation_form", quotation);

	}, 800);

});