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
                "kms": "kms",
                "variant": "variant",
                "accessory": "accessory",
                "discount_excluding_gst": "discount_excluding_gst",
                "registration_charges": "registration_charges",
                "ex_showroom_amount": "ex_showroom_amount",
                "ex_showroom_amount_net_of_discount": "ex_showroom_amount_net_of_discount"
            };

            Object.keys(fieldMap).forEach(key => {
                const value = record[key] !== undefined ? record[key] : 0;
                frappe.web_form.set_value(fieldMap[key], value);

                // Make field read-only
                const field = frappe.web_form.get_field(fieldMap[key]);
                if (field && field.$input) {
                    field.$input.prop("readonly", true);
                }
            });

            if (record.revised_quotation_vendor) {
                const filePath = record.revised_quotation_vendor;
                const fileName = filePath.split("/").pop();

                frappe.web_form.set_value("revised_quotation_vendor", filePath);

                setTimeout(() => {
                    const field = frappe.web_form.get_field("revised_quotation_vendor");
                    if (field) {
                        field.df.read_only = 1;
                        field.refresh();
                    }
                }, 300);

                const container = document.getElementById("quotation-file");
                if (container) {
                    container.innerHTML = `<a href="${filePath}" target="_blank">${fileName}</a>`;
                }
            }
        }
    });
});
