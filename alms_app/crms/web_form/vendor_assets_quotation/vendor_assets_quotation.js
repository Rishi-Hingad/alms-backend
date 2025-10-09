frappe.ready(function () {
    const params = new URLSearchParams(window.location.search);
    const employeeDetails = params.get("employee_details");

    if (!employeeDetails) return;

    frappe.call({
        method: "alms_app.crms.web_form.vendor_assets_quotation.vendor_assets_quotation.get_vendor_quotation",
        args: { employee_details: employeeDetails },
        callback: function (r) {
            if (!r.message) return;

            const record = r.message;

            const fieldMap = {
                "financed_amount": "financed_amount",
                "location": "location",
                "total_kms": "total_kms",
                "variant": "variant",
                "accessories": "accessories",
                "discount_excluding_gst": "discount_excluding_gst",
                "registration_charges": "registration_charges",
                "ex_showroom_amount": "ex_showroom_amount",
                "ex_showroom_amount_net_of_discount": "ex_showroom_amount_net_of_discount",
                "tenure_in_years": "tenure",
            };

            Object.keys(fieldMap).forEach(key => {
                const value = record[key] !== undefined ? record[key] : 0;
                frappe.web_form.set_value(fieldMap[key], value);

                const field = frappe.web_form.get_field(fieldMap[key]);
                if (field && field.$input) field.$input.prop("readonly", true);
            });

            if (record.revised_quotation_vendor) {
                const fieldname = "revised_quotation_vendor";
                const file_url = record.revised_quotation_vendor;
                const file_name = record.revised_quotation_vendor_name;

                frappe.web_form.set_value(fieldname, file_url);

                const field = frappe.web_form.get_field(fieldname);
                if (field) {
                    field.df.read_only = 1;
                    field.refresh();

                    if (field.$wrapper) {
                        field.$wrapper.empty();
                        const link = $(`<a href="${file_url}" target="_blank">${file_name}</a>`);
                        field.$wrapper.append(link);
                    }
                }
            }
        }
    });
});