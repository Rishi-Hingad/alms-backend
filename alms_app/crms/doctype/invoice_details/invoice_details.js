// Copyright (c) 2026, Rishi Hingad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice Details", {

    employee_name: function (frm) {

        if (!frm.doc.employee_name) return;

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Company and Employee Deduction",
                filters: {
                    employee_name: frm.doc.employee_name
                },
                fields: [
                    "quarterly_payment",
                    "employee_quarterly_payment"
                ],
                limit_page_length: 1
            },
            callback: function (r) {
                // console.log("Deduction record:", r.message);
                if (r.message && r.message.length) {

                    frm.set_value(
                        "company_contribution",
                        r.message[0].quarterly_payment || 0
                    );

                    frm.set_value(
                        "employee_contribution",
                        r.message[0].employee_quarterly_payment || 0
                    );
                }

            }
        });

    }

});