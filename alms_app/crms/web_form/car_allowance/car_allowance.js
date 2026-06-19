console.log("✅ car_allowance_form.js loaded");

frappe.ready(function () {
    function getEmployeeCodeFromURL() {
        const params = new URLSearchParams(window.location.search);
        return decodeURIComponent(params.get("employee_code") || "");
    }

    const employeeCode = getEmployeeCodeFromURL();
    if (employeeCode) {
        frappe.web_form.set_value('employee_code', employeeCode);

        frappe.call({
            method: "alms_app.crms.web_form.car_allowance.car_allowance.get_employee_details",
            args: { employee_code: employeeCode },
            callback: function (response) {
                const employeeDetails = response.message;
                if (employeeDetails) {
                    frappe.web_form.set_value('designation', employeeDetails[0].designation);
                    frappe.web_form.set_value('location', employeeDetails[0].location);
                    frappe.web_form.set_value('company_name', employeeDetails[0].company);
                    frappe.web_form.set_value('employee_reporting', employeeDetails[0].reporting_head);
                    frappe.web_form.set_value('contact_number', employeeDetails[0].contact_number);
                    frappe.web_form.set_value('email_id', employeeDetails[0].email_id);
                    frappe.web_form.set_value('department', employeeDetails[0].department);
                    frappe.web_form.set_value('eligibility', employeeDetails[0].eligibility);
                }
            }
        });
    }

    frappe.web_form.validate = function () {
        const employeeCode = frappe.web_form.get_value("employee_code");
        let exists = false;
        
        // Synchronous check before Frappe's native save
        frappe.call({
            method: "alms_app.crms.web_form.car_allowance.car_allowance.check_allowance_exists",
            args: { employee_code: employeeCode },
            async: false,
            callback: function (r) {
                if (r.message === "exists") {
                    exists = true;
                }
            }
        });

        if (exists) {
            frappe.show_alert({
                message: __('Allowance already exists.'),
                indicator: 'red'
            }, 3);
            setTimeout(() => { window.location.href = "/already-present"; }, 2000);
            return false; // Aborts native save
        }
        return true; // Proceeds to native save -> after_save
    };

    frappe.web_form.after_save = function () {
        const employeeCode = frappe.web_form.get_value("employee_code");
        frappe.call({
            method: "alms_app.crms.web_form.car_allowance.car_allowance.send_allowance_email",
            args: { employee_code: employeeCode },
            callback: function () {
                frappe.show_alert({
                    message: __('Your Car Allowance request was submitted successfully.'),
                    indicator: 'green'
                }, 3);
                setTimeout(() => { window.location.href = "/allowance"; }, 2000);
            }
        });
    };
});
