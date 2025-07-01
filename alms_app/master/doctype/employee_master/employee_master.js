// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt

function send_email(frm, email_send_to) {
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name: frm.doc.name,
            email_send_to: email_send_to,
        },
        callback: function (response) {
            if (!response.exc) {
                frappe.msgprint("Email sent successfully!");
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
}


frappe.ui.form.on("Employee Master", {
    onload(frm) {
    },

    refresh: function (frm) {
        updateEmailButton(frm);
        if (frm.doc.designation) {

        }
    },

    status: function (frm) {
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

            const eligibility = parseFloat(frm.doc.eligibility);
            if (!eligibility || eligibility < 100000) {
                frappe.msgprint({
                    title: "Ineligible",
                    indicator: "orange",
                    message: "Email cannot be sent. Eligibility is either not set or less than ₹1,00,000."
                });
                return;
            }
            frm.set_value("status", "Sent");
            send_email(frm, "To Employee")
            frm.save_or_update();
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