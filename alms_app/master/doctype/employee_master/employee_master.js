// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt
frappe.ui.form.on("Employee Master", {
    onload(frm) {
        const eligibilityMap = {
            "Manager": 500000,
            "Senior Manager": 750000,
            "Deputy General Manager": 1000000,
            "General Manager": 1500000,
            "Additional General Manager": 1500000,
            "Vice President": 2000000,
            "Senior General Manager": 2000000,
        };

        const eligibility = eligibilityMap[frm.doc.designation] || 0;

        if (eligibility > 0 && frm.doc.eligibility !== eligibility) {
            frm.set_value("eligibility", eligibility);
        }
    },

    designation(frm) {
        const eligibilityMap = {
            "Manager": 500000,
            "Senior Manager": 750000,
            "Deputy General Manager": 1000000,
            "General Manager": 1500000,
            "Additional General Manager": 1500000,
            "Vice President": 2000000,
            "Senior General Manager": 2000000,
        };

        const eligibility = eligibilityMap[frm.doc.designation] || 0;

        if (eligibility > 0) {
            frm.set_value("eligibility", eligibility);
        }
    },

    refresh: function(frm) {
        updateEmailButton(frm);
    },
    
    status: function(frm) {
        updateEmailButton(frm);
    }
});
function updateEmailButton(frm) {
    
    frm.remove_custom_button("Send Email");
    frm.remove_custom_button("Email Sent");

    if (frm.doc.status === "Sent") {
        frm.add_custom_button("Email Sent", null)
            .addClass("btn-disabled")
            .css({
                "background-color": "#daf0e1",
                "color": "#16794c",
                "border-color": "darkgreen",
                "cursor": "not-allowed",
                "font-weight": "semibold",
                "text-transform": "uppercase",
            })
            .html('<i class="fa fa-check"></i> Email Sent');
    } else {
        frm.add_custom_button("Send Email", () => {
            if (!frm.doc.email_id) {
                frappe.msgprint("Email address is not set for this employee.");
                return;
            }
        frappe.call({
            method: "alms_app.master.doctype.employee_master.employee_master.send_email",
            args: {
                name: frm.doc.name,
            },
            callback: function (response) {
                if (!response.exc) {
                    frappe.msgprint("Email sent successfully!");
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: "Error",
                        indicator: "red",
                        message: response.exc || "An unknown error occurred while sending the email.",
                    });
                }
            },
            error: function (error) {
                frappe.msgprint({
                    title: "Error",
                    indicator: "red",
                    message: error.message || "An unknown error occurred while sending the email.",
                });
            },
        });
    })
    .css({
        "background-color": "#afd1f5",
        "color": "#004ea1",
        "border-color": "#007bff",
        "cursor": "pointer",
        "font-weight": "semibold",
        "text-transform": "uppercase",
    });
}
}