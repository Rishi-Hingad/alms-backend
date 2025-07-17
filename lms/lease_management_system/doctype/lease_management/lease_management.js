// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Lease Management", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Lease Management", {
    // vendor_code: function(frm) {
    //     if (frm.doc.vendor_code) {
    //         // Method 1: Using add_fetch (RECOMMENDED)
    //         frm.add_fetch('vendor_code', 'property_code', 'property_code');
            
    //         // The above line automatically fetches 'property_id' field from 
    //         // the Vendor document and sets it to 'property_id' field in current form
    //     } else {
    //         // Clear property_id when vendor_id is cleared
    //         frm.set_value('property_code', '');
    //     }
    // }
    refresh: function (frm) {     
        frm.set_query("property_code", function () {
        return {
            filters: {
            vendor_code: frm.doc.vendor_code
            }
        }});
        // frm.add_custom_button(__('My Custom Button'), function() {
        //         // Define action for the button
        //         frappe.msgprint(__('Button clicked!'));
        //     });

        // });
        frm.add_custom_button(__('Generate Report'), function() {
            frappe.call({
                method: 'lms.lease_management_system.doctype.lease_management.lease_management.generate_report',
                args: {
                    docname: frm.doc.name
                },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint(__(r.message));
                    }else {
                        frappe.msgprint(__('Failed to generate report.'));
                    }
                }
            });
                // frappe.msgprint(__('Button clicked!'));
        });
        
    },
   
    
    // property_code: function(frm) {
    //     if (frm.doc.property_code) {
    //         // Fetch the 'city' field from 'Property Master' where 'name' matches the 'property_code'
    //         frappe.db.get_value("Property Master", {
    //             "name": frm.doc.property_code  // Match 'name' field in Property Master with 'property_code'
    //         }, "city", function(r) {
    //             if (r && r.city) {
    //                 // If 'city' exists, set it on the virtual 'city' field in Lease Management form
    //                 frm.set_value("city", r.city);
    //                 frm.refresh_field("city");
    //             }
    //         });
    //     } else {
    //         // If 'property_code' is cleared, reset the 'city' field in Lease Management
    //         frm.set_value("city", "");
    //         frm.refresh_field("city");
    //     }
    // }

    // property_code:function(frm){
    //     if(frm.doc.property_code){
    //         frappe.db.get_value("Property Master",{
    //             "name":frm.doc.property_code
    //         },"id",function(r){
    //             if(r && r.property_code){
    //                 frm.set_value("city",r.city);
    //                 frm.refresh_field("city");
    //             }
    //         });
    //     }else{
    //         frm.set_value("city","");
    //         frm.refresh_field("city");
    //     }
    // }
});