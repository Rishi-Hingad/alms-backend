console.log("✅ car_indent_form.js loaded-----");

frappe.ready(function () {
    function getEmployeeCodeFromURL() {
        const params = new URLSearchParams(window.location.search);
        return decodeURIComponent(params.get("employee_code") || "");
    }

    const employeeCode = getEmployeeCodeFromURL();
    if (employeeCode) {
        frappe.web_form.set_value('employee_code', employeeCode);

        frappe.call({
            method: "lease_app.crms.web_form.car_indent_form.car_indent_form.get_employee_details",
            args: { employee_code: employeeCode },
            callback: function (response) {
                const employeeDetails = response.message;
                if (employeeDetails) {
                    frappe.web_form.set_value('designation', employeeDetails[0].designation);
                    frappe.web_form.set_value('eligibility', employeeDetails[0].eligibility);
                    frappe.web_form.set_value('ex_showroom_price', employeeDetails[0].eligibility);
                    frappe.web_form.set_value('location', employeeDetails[0].location);
                    frappe.web_form.set_value('company_name', employeeDetails[0].company);
                    frappe.web_form.set_value('employee_reporting', employeeDetails[0].reporting_head);
                    frappe.web_form.set_value('contact_number', employeeDetails[0].contact_number);
                    frappe.web_form.set_value('email_id', employeeDetails[0].email_id);
                    frappe.web_form.set_value('department', employeeDetails[0].department);
                }
            }
        });
    }

    frappe.web_form.on("ex_showroom_price", calculate_totals);
    frappe.web_form.on("discount", calculate_totals);
    frappe.web_form.on("tcs", calculate_totals);
    frappe.web_form.on("registration_charges", calculate_totals);
    frappe.web_form.on("accessories", calculate_totals);

    function formatINR(amount) {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
    }

    function calculate_totals() {
        const ex_showroom_price = parseFloat(frappe.web_form.get_value('ex_showroom_price')) || 0;
        const discount = parseFloat(frappe.web_form.get_value('discount')) || 0;
        const tcs = parseFloat(frappe.web_form.get_value('tcs')) || 0;
        const registration_charges = parseFloat(frappe.web_form.get_value('registration_charges')) || 0;
        const accessories = parseFloat(frappe.web_form.get_value('accessories')) || 0;

        const net_ex_showroom_price = ex_showroom_price - discount + tcs;
        const finance_amount = net_ex_showroom_price + registration_charges + accessories;

        frappe.web_form.set_value('net_ex_showroom_price', net_ex_showroom_price);
        frappe.web_form.set_value('finance_amount', finance_amount);
        frappe.web_form.set_value('net_ex_showroom_price_inr', formatINR(net_ex_showroom_price));
        frappe.web_form.set_value('finance_amount_inr', formatINR(finance_amount));
    }

    calculate_totals();

    frappe.web_form.validate = function () {
        const employeeCode = frappe.web_form.get_value("employee_code");
        let exists = false;
        
        frappe.call({
            method: "lease_app.crms.web_form.car_indent_form.car_indent_form.check_indent_exists",
            args: { employee_code: employeeCode },
            async: false,
            callback: function (response) {
                if (response.message === "redirect") {
                    exists = true;
                }
            }
        });

        if (exists) {
            frappe.show_alert({
                message: __('You already have an active indent.'),
                indicator: 'red'
            }, 3);
            setTimeout(() => { window.location.href = "/already-present"; }, 2000);
            return false;
        }
        return true;
    };

    frappe.web_form.after_save = function () {
        const employeeCode = frappe.web_form.get_value("employee_code");
        frappe.call({
            method: "lease_app.crms.web_form.car_indent_form.car_indent_form.send_email_to_reporting_head",
            args: { doc: employeeCode },
            callback: function () {
                frappe.show_alert({
                    message: __('Your Car Indent request was submitted successfully.'),
                    indicator: 'green'
                }, 3);
                setTimeout(() => { window.location.href = "/allowance"; }, 2000);
            },
            error: function () {
                frappe.show_alert({
                    message: __('Error sending car indent email.'),
                    indicator: 'red'
                }, 3);
            }
        });
    };
});
