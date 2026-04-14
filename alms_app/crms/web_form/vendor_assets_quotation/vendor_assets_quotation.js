frappe.ready(function () {
    const params = new URLSearchParams(window.location.search);
    const employeeDetails = params.get("employee_details");

    if (!employeeDetails) return;
    add_upload_button();

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

function add_upload_button() {
    const interval = setInterval(() => {

        const form = $("form:visible").first();

        if (form.length) {
            clearInterval(interval);

            // Prevent duplicate
            if ($("#upload-excel-btn").length) return;

            const btn = $(`
                <div id="upload-excel-btn" style="margin-bottom: 15px;">
                    <button class="btn btn-primary" type="button">
                        Upload Quotation in Excel format
                    </button>
                </div>
            `);

            form.prepend(btn);

            btn.on("click", function () {
                open_excel_uploader();
            });

            console.log("✅ Button successfully added to form");
        }

    }, 500);
}

function open_excel_uploader() {
    new frappe.ui.FileUploader({
        allow_multiple: false,
        as_dataurl: false,
        restrictions: {
            allowed_file_types: ['.xls', '.xlsx']
        },
        on_success: function(file) {
            console.log("Uploaded File:", file);

            // file.file_url is what you need
            process_excel(file.file_url);
        }
    });
}


function process_excel(file_url) {
    frappe.call({
        method: "alms_app.api.car_quotation.process_vendor_excel",
        args: {
            file_url: file_url
        },
        callback: function (r) {
            if (r.message) {
                frappe.msgprint({
                    title: "Success",
                    indicator: "green",
                    message: "Excel processed successfully!"
                });

                // Optional: auto-fill form after upload
                // location.reload();
            }
        }
    });
}