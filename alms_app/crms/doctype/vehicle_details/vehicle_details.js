frappe.ui.form.on("Vehicle Details", {
    car_allotment_letter: function(frm) {
        if (frm.doc.car_allotment_letter) {
            frappe.call({
                method: "alms_app.crms.doctype.vehicle_details.vehicle_details.send_car_allotment_email",
                args: {
                    docname: frm.doc.name,
                    employee_code: frm.doc.employee_code_and_name,
                    file_url: frm.doc.car_allotment_letter
                },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint(r.message || "Car Allotment Letter email sent successfully.");
                    }
                }
            });
        }
    },

    rc_book: function(frm) {
        if (frm.doc.rc_book) {
            frappe.call({
                method: "alms_app.crms.doctype.vehicle_details.vehicle_details.send_rc_book_email",
                args: {
                    docname: frm.doc.name,
                    employee_code: frm.doc.employee_code_and_name,
                    file_url: frm.doc.rc_book
                },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint(r.message || "RC Book email sent successfully.");
                    }
                }
            });
        }
    }
});