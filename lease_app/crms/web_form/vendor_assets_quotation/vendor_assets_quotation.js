frappe.ready(function () {

    const params = new URLSearchParams(window.location.search);
    const employeeDetails = params.get("employee_details");
    const quotationId = params.get("quotation_id");
    const isRevised = params.get("is_revised");

    const lockedFields = new Set([
        "revised_financed_amount",
        "location",
        "total_kilometers",
        "make",
        "revised_accessories",
        "revised_discount",
        "revised_registration_charges",
        "revised_ex_show_room_price",
        "revised_net_ex_showroom_price",
        "tenure_in_years"
    ]);

    if (!employeeDetails) return;

    add_upload_button();

    let recordData = null;
    let formReady = false;

    // fetch data
    frappe.call({
        method: "lease_app.crms.web_form.vendor_assets_quotation.vendor_assets_quotation.get_vendor_quotation",
        args: {
            employee_details: employeeDetails,
            quotation_id: quotationId
        },
        callback: function (r) {
            if (!r.message) return;

            recordData = r.message;

            tryFill();
        }
    });

    // hook web form load safely
    $(document).on("form-rendered", function () {
        formReady = true;
        tryFill();
    });

    // fallback (because Frappe is inconsistent here)
    setTimeout(() => {
        formReady = true;
        tryFill();
    }, 1500);

    function tryFill() {

        if (!formReady || !recordData) return;

        Object.keys(recordData).forEach(key => {

            const field = frappe.web_form.get_field(key);
            if (!field) return;

            const value = recordData[key];

            // set value
            frappe.web_form.set_value(key, value);

            // lock only specific fields
            if (lockedFields.has(key)) {

                if (field.$input) {
                    field.$input.prop("readonly", true);
                }

                if (field.$wrapper) {
                    field.$wrapper.css({
                        "pointer-events": "none",
                        "opacity": "0.85"
                    });
                }
            }
        });

        if (recordData.revised_quotation_vendor) {
            frappe.web_form.set_value(
                "revised_quotation_vendor",
                recordData.revised_quotation_vendor
            );

            const fileField = frappe.web_form.get_field("revised_quotation_vendor");
            if (fileField && fileField.$wrapper) {
                // Wait briefly for set_value to render the file link, then hide buttons
                setTimeout(() => {
                    fileField.$wrapper.find('.btn-attach, [data-action="clear_attachment"]').hide();
                }, 100);
            }
        }
    }

    // Disable save button and show "Saving..." on click
    $(document).on("click", ".submit-btn", function () {
        let $btn = $(this);
        let form = $('.web-form')[0];

        // Ensure the form is valid before changing the button state
        if (form && form.checkValidity && !form.checkValidity()) {
            return;
        }

        let originalText = $btn.text();
        $btn.text("Saving...");
        $btn.css("pointer-events", "none");
        $btn.addClass("disabled");

        // Revert text if the button is re-enabled (e.g. on validation error from backend)
        let checkInterval = setInterval(() => {
            if (!$btn.prop("disabled") && !window.saving) {
                $btn.text(originalText);
                $btn.css("pointer-events", "auto");
                $btn.removeClass("disabled");
                clearInterval(checkInterval);
            }
        }, 500);

        // Safety cleanup for interval
        setTimeout(() => {
            clearInterval(checkInterval);
            $btn.css("pointer-events", "auto");
            $btn.removeClass("disabled");
            $btn.text(originalText);
        }, 15000);
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
        on_success: function (file) {
            console.log("Uploaded File:", file);

            // file.file_url is what you need
            process_excel(file.file_url);
        }
    });
}


function process_excel(file_url) {
    frappe.call({
        method: "lease_app.api.car_quotation.process_vendor_excel",
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

frappe.web_form.after_save = function () {

    const doc = frappe.web_form.doc;

    const params = new URLSearchParams(window.location.search);
    const isRevised = params.get("is_revised");

    const email_phase = isRevised == "1" ? "Revised" : "Initial";

    console.log("Vendor submitted quotation:", doc.name, "Phase:", email_phase);

    send_email(
        doc.name,
        doc.finance_company,
        doc.finance_company,
        email_phase
    );
};

function send_email(quotation_name, finance_company, vendor_name, email_phase) {
    const doc = frappe.web_form.doc;
    frappe.call({
        method: "lease_app.lease_app.api.emailsService.email_sender",
        args: {
            name: doc.employee_details,
            email_send_to: "Finance Fill Quotation Acknowledgement",
            payload: JSON.stringify({
                vendors: [vendor_name],
                email_phase: email_phase
            })
        },
        callback: function (r) {
            if (r.message && r.message.status === "success") {
                console.log("Email sent successfully!");
            } else {
                console.error("Error sending email:", r.message);
            }
        }
    });
}