frappe.ready(function() {
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
            callback: function(response) { 
                console.log('API Response:', response); 
                const employeeDetails = response.message;
                if (employeeDetails) {
                    // frappe.web_form.set_value('designation', employeeDetails.designation);
                    // frappe.web_form.set_value('eligibility', employeeDetails.eligibility);
                    // frappe.web_form.set_value('location', employeeDetails.location);
                    // frappe.web_form.set_value('company_name', employeeDetails.company);
                    // frappe.web_form.set_value('contact_number', employeeDetails.contact_number);
                    // frappe.web_form.set_value('email_id', employeeDetails.email_id);
                    // frappe.web_form.set_value('department', employeeDetails.employee_department);


                    // frappe.web_form.set_value('designation', employeeDetails[0].custom_edesignation);
                    frappe.web_form.set_value('designation', employeeDetails[0].designation);
                    frappe.web_form.set_value('eligibility', employeeDetails[1].eligibility);
                    frappe.web_form.set_value('location', employeeDetails[0].location);
                    frappe.web_form.set_value('company_name', employeeDetails[0].company);
                    frappe.web_form.set_value('contact_number', employeeDetails[0].contact_number);
                    frappe.web_form.set_value('email_id', employeeDetails[0].email_id);
                    // frappe.web_form.set_value('department', employeeDetails[0].custom_edepartment);
                    frappe.web_form.set_value('department', employeeDetails[0].department);

					frappe.web_form.set_df_property('designation', 'read_only', true);
					frappe.web_form.set_df_property('eligibility', 'read_only', true);
					frappe.web_form.set_df_property('location', 'read_only', true);
					frappe.web_form.set_df_property('company_name', 'read_only', true);
					frappe.web_form.set_df_property('contact_number', 'read_only', true);
					frappe.web_form.set_df_property('email_id', 'read_only', true);
					frappe.web_form.set_df_property('department', 'read_only', true);
                }
            },
            error: function(error) {
                console.log('Error fetching employee details:', error);
            }
        });
    }

    frappe.web_form.on("ex_showroom_price", calculate_totals);
    frappe.web_form.on("discount", calculate_totals);
    frappe.web_form.on("tcs", calculate_totals);
    frappe.web_form.on("registration_charges", calculate_totals);
    frappe.web_form.on("accessories", calculate_totals);
	
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
}

calculate_totals();

frappe.web_form.on("submit", function () {
    const employeeCode = frappe.web_form.get_value("employee_code");

    frappe.call({
        method: "alms_app.crms.web_form.car_indent_form.car_indent_form.send_email_to_reporting_head",
        args: {
            employee_code: employeeCode
        },
        callback: function (response) {
            console.log("Email sent successfully:", response);
        },
        error: function (error) {
            console.log("Error sending email:", error);
        }
    });
});

// frappe.web_form.on("submit", function (form) {
//     const employeeCode = frappe.web_form.get_value("employee_code");

//     frappe.call({
//         method: "alms_app.crms.web_form.car_indent_form.car_indent_form.check_indent_exists",
//         args: {
//             employee_code: employeeCode
//         },
//         callback: function (response) {
//             const indentExists = response.message;

//             if (indentExists) {
//                 frappe.msgprint("An indent form already exists for this employee.");
//                 // Prevent submission
//                 form.prevent_default = true;
//             } else {
//                 // Proceed to send email
//                 frappe.call({
//                     method: "alms_app.crms.web_form.car_indent_form.car_indent_form.send_email_to_reporting_head",
//                     args: {
//                         employee_code: employeeCode
//                     },
//                     callback: function (response) {
//                         console.log("Email sent successfully:", response);
//                     },
//                     error: function (error) {
//                         console.log("Error sending email:", error);
//                     }
//                 });
//             }
//         },
//         error: function (error) {
//             console.log("Error checking indent existence:", error);
//         }
//     });
// });

});
