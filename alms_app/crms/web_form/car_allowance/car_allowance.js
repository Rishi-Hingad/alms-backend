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
                }
            }
        });
    }

    frappe.web_form.validate = function () {
        const employeeCode = frappe.web_form.get_value("employee_code");

        return new Promise((resolve, reject) => {
            frappe.call({
                method: "alms_app.crms.web_form.car_allowance.car_allowance.create_allowance_entry",
                args: { employee_code: employeeCode },
                callback: function (res) {
                    if (res.message?.status === "success") {
                        frappe.msgprint("Your Car Allowance request was submitted successfully.");
                        setTimeout(() => { window.location.href = "/allowance"; }, 2000);
                        resolve();
                    } else {
                        frappe.msgprint(res.message?.message || "Allowance already exists.");
                        setTimeout(() => { window.location.href = "/already-present"; }, 2000);
                        reject("Allowance already exists");
                    }
                }
            });
        });
    };
});
