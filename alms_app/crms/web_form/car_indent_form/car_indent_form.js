frappe.ready(function () {
    const urlParams = new URLSearchParams(window.location.search);
    const employeeCodeFromURL = urlParams.get('employee_code');

    if (employeeCodeFromURL) {
        frappe.web_form.set_value('employee_code', employeeCodeFromURL);
        console.log('Employee Code:', employeeCodeFromURL);

        frappe.call({
            method: "alms_app.crms.web_form.car_indent_form.car_indent_form.get_employee_details",
            args: {
                employee_code: employeeCodeFromURL
            },
            callback: function (response) {
                console.log('API Response:', response);
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

                    frappe.web_form.set_df_property('designation', 'read_only', true);
                    frappe.web_form.set_df_property('ex_showroom_price', true);
                    frappe.web_form.set_df_property('eligibility', 'read_only', true);
                    frappe.web_form.set_df_property('location', 'read_only', true);
                    frappe.web_form.set_df_property('company_name', 'read_only', true);
                    frappe.web_form.set_df_property('employee_reporting', 'read_only', true);
                    frappe.web_form.set_df_property('contact_number', 'read_only', true);
                    frappe.web_form.set_df_property('email_id', 'read_only', true);
                    frappe.web_form.set_df_property('department', 'read_only', true);
                }
            },
            error: function (error) {
                console.log('Error fetching employee details:', error);
            }
        });
    }

    frappe.web_form.on("ex_showroom_price", calculate_totals);
    frappe.web_form.on("discount", calculate_totals);
    frappe.web_form.on("tcs", calculate_totals);
    frappe.web_form.on("registration_charges", calculate_totals);
    frappe.web_form.on("accessories", calculate_totals);

    function formatINR(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 2
        }).format(amount);
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
        console.log('Formatted INR:', formatINR(100000));

        frappe.web_form.set_value('net_ex_showroom_price_inr', formatINR(net_ex_showroom_price));
        frappe.web_form.set_value('finance_amount_inr', formatINR(finance_amount));
    }
    
    calculate_totals();

    // frappe.web_form.validate = () => {
    //     const employeeCode = frappe.web_form.get_value("employee_code");
    //     const formType = frappe.web_form.get_value("form_type");
    
    //     console.log("Form Type:", formType);
    
    //     if (formType === "Allowance") {
    //         frappe.call({
    //             method: "alms_app.crms.web_form.car_indent_form.car_indent_form.send_allowance_email",
    //             args: {
    //                 employee_code: employeeCode
    //             },
    //             callback: function () {
    //                 frappe.msgprint("Your Car Allowance request was submitted successfully.");
    //                 setTimeout(() => {
    //                     window.location.href = "/allowance";
    //                 }, 10000);
    //             },
    //             error: function (error) {
    //                 console.error("Error sending allowance email:", error);
    //                 frappe.msgprint("Something went wrong while submitting the allowance form.");
    //             }
    //         });
    //         return false;
    //     }
    
    //     return new Promise((resolve, reject) => {
    //         if (formType === "Car") {
    //             // Check if the Car indent form exists
    //             frappe.call({
    //                 method: "alms_app.crms.web_form.car_indent_form.car_indent_form.check_indent_exists",
    //                 args: { employee_code: employeeCode },
    //                 callback: function (response) {
    //                     if (response.message === "redirect") {
    //                         // If indent exists, prevent form submission and redirect
    //                         setTimeout(() => {
    //                             window.location.href = "/already-present";  // Redirect when indent exists
    //                         }, 30000);
    //                         reject();  // Reject to stop form submission
    //                     } else {
    //                         // If indent does not exist, proceed with sending email
    //                         frappe.call({
    //                             method: "alms_app.crms.web_form.car_indent_form.car_indent_form.send_email_to_reporting_head",
    //                             args: { employee_code: employeeCode },
    //                             callback: function () {
    //                                 // After email is sent, allow form submission to proceed
    //                                 resolve(); 
    //                             },
    //                             error: function (error) {
    //                                 console.error("Error sending email:", error);
    //                                 frappe.msgprint("Something went wrong while sending the email.");
    //                                 reject(); // Reject if email fails
    //                             }
    //                         });
    //                     }
    //                 },
    //                 error: function (error) {
    //                     console.error("Error checking indent existence:", error);
    //                     reject(); // Reject on error checking indent
    //                 }
    //             });
    //         } else {
    //             frappe.msgprint("Invalid form type selected.");
    //             reject(); // Reject if form type is invalid
    //         }
    //     }); 
    // };        
    frappe.web_form.validate = () => {
        const employeeCode = frappe.web_form.get_value("employee_code");
        const formType = frappe.web_form.get_value("form_type");
    
        console.log("Form Type:", formType);
        if (formType === "Allowance") {
            frappe.call({
                method: "alms_app.crms.web_form.car_indent_form.car_indent_form.send_allowance_email",
                args: { employee_code: employeeCode },
                callback: function () {
                    frappe.msgprint("Your Car Allowance request was submitted successfully.");
                    setTimeout(() => {
                        window.location.href = "/allowance";
                    }, 10000);
                },
                error: function (error) {
                    console.error("Error sending allowance email:", error);
                    frappe.msgprint("Something went wrong while submitting the allowance form.");
                }
            });
            return false;
        }
    
        return new Promise((resolve, reject) => {
            if (formType === "Car") {
                frappe.call({
                    method: "alms_app.crms.web_form.car_indent_form.car_indent_form.check_indent_exists",
                    args: { employee_code: employeeCode },
                    callback: function (response) {
                        if (response.message === "redirect") {
                            console.log("Indent exists, redirecting...");
                            setTimeout(() => {
                                window.location.href = "/already-present";
                            }, 1000);
                            reject("Indent exists");
                        } else {
                            console.log("Indent does not exist, sending email...");
                            frappe.call({
                                method: "alms_app.crms.web_form.car_indent_form.car_indent_form.send_email_to_reporting_head",
                                args: { employee_code: employeeCode },
                                callback: function () {
                                    console.log("Email sent, resolving form submission...");
                                    resolve();
                                },
                                error: function (error) {
                                    console.error("Error sending email:", error);
                                    frappe.msgprint("Something went wrong while sending the email.");
                                    reject(error);
                                }
                            });
                        }
                    },
                    error: function (error) {
                        console.error("Error checking indent existence:", error);
                        reject(error);
                    }
                });
            } else {
                frappe.msgprint("Invalid form type selected.");
                reject("Invalid form type");
            }
        });
    };
    
});
