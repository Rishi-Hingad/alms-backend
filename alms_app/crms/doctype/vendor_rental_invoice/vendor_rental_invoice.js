// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vendor Rental Invoice", {
    // Trigger when invoice_date_from is changed
    "invoice_date_from": function(frm) {
        calculate_billing_days(frm);
    },

    // Trigger when invoice_date_to is changed
    "invoice_date_to": function(frm) {
        calculate_billing_days(frm);
    },

    refresh: function(frm) {
        // Calculate billing days on refresh if both dates are already set
        calculate_billing_days(frm);
    }
});

function calculate_billing_days(frm) {
    // Check if both invoice_date_from and invoice_date_to are present
    if (frm.doc.invoice_date_from && frm.doc.invoice_date_to) {
        // Convert invoice_date_from and invoice_date_to to Date objects
        var date_from_obj = new Date(frm.doc.invoice_date_from);
        var date_to_obj = new Date(frm.doc.invoice_date_to);

        // Log the date values for debugging
        console.log("Invoice Date From:", frm.doc.invoice_date_from);
        console.log("Invoice Date To:", frm.doc.invoice_date_to);
        console.log("Date From Object:", date_from_obj);
        console.log("Date To Object:", date_to_obj);

        // Calculate the day difference manually
        var time_diff = date_to_obj.getTime() - date_from_obj.getTime();
        var days_diff = time_diff / (1000 * 3600 * 24); // Convert time difference to days

        // Add 1 to include the start date
        days_diff += 1;

        // Ensure the days difference is not negative
        if (days_diff < 0) {
            days_diff = 0; // Set to 0 if negative
        }

        // Log the calculated day difference for debugging
        console.log("Days Difference (including start date):", days_diff);

        // Set the calculated value in the "number_of_billing_days" field and refresh it
        frm.set_value("number_of_billing_days", days_diff);
        frm.refresh_field("number_of_billing_days");
    } else {
        console.log("Invoice dates are missing or incomplete.");
    }
}
