// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Car Quotation", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Car Quotation', {
    refresh: function(frm) {
        // Initially hide the fields using toggle_display(false)
        let fieldsToHide = [
            'Finance Company', 'Employee Details', 'Location', 'KMS', 'Variant', 'Quote', 
            'Interest Rate', 'Tenure', 'Base Price Excluding GST', 'GST', 'Ex-Showroom Amount', 
            'Accessory', 'Discount (Excluding GST)', 'Base Price Less Discounts', 'Total Discount', 
            'Ex-Showroom Amount(Net of Discount)', 'Registration Charges', 'Residual Value', 'Percent', 
            'Financed Amount', 'EMI (Financing)', 'Finance EMI - Road Tax', 'GST and Cess', 'Insurance', 
            'Fleet Management (Repairs and Tyres)', '24x7 Assist', 'Pickup & Drop', 'Std Relief Car (Non Accdt)', 
            'GST on FMS', 'Total EMI'
        ];

        // Hide all fields initially
        fieldsToHide.forEach(function(field) {
            frm.toggle_display(field, false);
        });

        // Add upload button
        frm.add_custom_button('Upload Excel', function() {
            frm.upload_data();
        });
    },

    upload_data: function(frm) {
        // This method will call the backend to handle the file upload
        frappe.call({
            doc: frm.doc,
            method: 'upload_data', // Ensure that this method exists in the backend
            freeze: true,
            freeze_message: 'Uploading and processing data...',
            callback: function(r) {
                if (r.message) {
                    // If data is uploaded successfully, show the fields using toggle_display(true)
                    let fieldsToShow = [
                        'Finance Company', 'Employee Details', 'Location', 'KMS', 'Variant', 'Quote', 
                        'Interest Rate', 'Tenure', 'Base Price Excluding GST', 'GST', 'Ex-Showroom Amount', 
                        'Accessory', 'Discount (Excluding GST)', 'Base Price Less Discounts', 'Total Discount', 
                        'Ex-Showroom Amount(Net of Discount)', 'Registration Charges', 'Residual Value', 'Percent', 
                        'Financed Amount', 'EMI (Financing)', 'Finance EMI - Road Tax', 'GST and Cess', 'Insurance', 
                        'Fleet Management (Repairs and Tyres)', '24x7 Assist', 'Pickup & Drop', 'Std Relief Car (Non Accdt)', 
                        'GST on FMS', 'Total EMI'
                    ];

                    // Show all fields after upload
                    fieldsToShow.forEach(function(field) {
                        frm.toggle_display(field, true);
                    });
                    frm.refresh_fields(); // Ensure the form updates with the changes
                }
            }
        });
    }
});
