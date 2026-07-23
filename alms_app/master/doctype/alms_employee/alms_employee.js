// Copyright (c) 2025, Blue Phoenix and contributors
// For license information, please see license.txt

frappe.ui.form.on("ALMS Employee", {
    refresh(frm) {
        if (!frm.is_new()) {
            if (frappe.session.user === "Administrator" || frappe.user.has_role("Administrator") || frappe.user.has_role("System Manager")) {
                if (frm.doc.user_id || frm.doc.company_email) {
                    let cred_btn = frm.add_custom_button(__("Send Credential Email"), function () {
                        if (!frm.doc.create_user) {
                            frappe.msgprint({
                                title: "Action Required",
                                indicator: "orange",
                                message: "Please check 'Create User' to enable sending credentials."
                            });
                            return;
                        }
                        frappe.call({
                            method: "alms_app.master.doctype.alms_employee.alms_employee.send_credential_email",
                            args: {
                                employee_names: [frm.doc.name]
                            },
                            callback: function(r) {
                                if (r.message && r.message.status === "error") {
                                    frappe.msgprint({
                                        title: "Error",
                                        indicator: "red",
                                        message: "Failed to send Credential Email: " + r.message.message
                                    });
                                } else if (!r.exc) {
                                    frappe.msgprint("Credential Email sent successfully!");
                                } else {
                                    frappe.msgprint("Failed to send Credential Email.");
                                }
                            }
                        });
                    });

                    if (cred_btn) {
                        if (!frm.doc.create_user) {
                            cred_btn.addClass("btn-disabled").css("cursor", "not-allowed");
                        } else {
                            cred_btn.removeClass("btn-disabled").css("cursor", "pointer");
                        }
                    }
                }
            }

            updateEmailButton(frm);
        }
    },

    eligibility_email_status: function (frm) {
        if (!frm.is_new()) updateEmailButton(frm);
    },

    create_user: function (frm) {
        frm.trigger("refresh");
    },

    status: function (frm) {
        if (!frm.is_new()) updateEmailButton(frm);
    },
    
    eligibility: function (frm) {
        if (!frm.is_new()) updateEmailButton(frm);
    }
});

function send_eligibility_email(frm, email_send_to, btn) {
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name: frm.doc.name,
            email_send_to: email_send_to,
        },
        callback: function (response) {
            if (response.message && response.message.status === "error") {
                if (btn) {
                    btn.removeClass("btn-disabled").prop("disabled", false).text("Send Eligibility Email").css({
                        "background-color": "#afd1f5",
                        "color": "#004ea1",
                        "border-color": "#007bff",
                        "cursor": "pointer",
                        "pointer-events": "auto"
                    });
                }
                frappe.msgprint({
                    title: "Error",
                    indicator: "red",
                    message: "Failed to send Eligibility Email: " + response.message.message
                });
            } else if (!response.exc) {
                frappe.show_alert({
                    message: __("Eligibility Email sent successfully!"),
                    indicator: "green"
                });
                frm.set_value("eligibility_email_status", "Sent");
                frm.save_or_update();
            } else {
                if (btn) {
                    btn.removeClass("btn-disabled").prop("disabled", false).text("Send Eligibility Email").css({
                        "background-color": "#afd1f5",
                        "color": "#004ea1",
                        "border-color": "#007bff",
                        "cursor": "pointer",
                        "pointer-events": "auto"
                    });
                }
                frappe.msgprint({
                    title: __("Error"),
                    indicator: "red",
                    message: __("Failed to send Eligibility Email.")
                });
            }
        },
        error: function (error) {
            if (btn) {
                btn.removeClass("btn-disabled").prop("disabled", false).text("Send Eligibility Email").css({
                    "background-color": "#afd1f5",
                    "color": "#004ea1",
                    "border-color": "#007bff",
                    "cursor": "pointer",
                    "pointer-events": "auto"
                });
            }
            frappe.msgprint({
                title: "Error",
                indicator: "red",
                message: error.message || "An unknown error occurred while sending the email.",
            });
        },
    });
}

function updateEmailButton(frm) {
    frm.remove_custom_button("Send Eligibility Email");
    frm.remove_custom_button("Eligibility Email Sent");

    // Don't show if Employee is Inactive or Left
    if (frm.doc.status === "Inactive" || frm.doc.status === "Left") {
        return;
    }

    if (frm.doc.eligibility_email_status === "Sent") {
        let btn = frm.add_custom_button("Eligibility Email Sent", function () { });
        if (btn) {
            btn.addClass("btn-disabled")
                .css({
                    "background-color": "#daf0e1",
                    "color": "#16794c",
                    "border-color": "darkgreen",
                    "cursor": "not-allowed",
                    "font-weight": "semibold",
                    "text-transform": "uppercase",
                })
                .html('<i class="fa fa-check"></i> Email Sent');
        }
    } else {
        let btn = frm.add_custom_button("Send Eligibility Email", () => {
            if (!frm.doc.company_email && !frm.doc.personal_email) {
                frappe.msgprint("Email address is not set for this employee.");
                return;
            }

            const eligibility = parseFloat(frm.doc.eligibility);
            if (!eligibility || eligibility < 500000) {
                frappe.msgprint({
                    title: "Ineligible",
                    indicator: "orange",
                    message: "Email cannot be sent. Eligibility is either not set or less than ₹5,00,000."
                });
                return;
            }
            
            if (btn) {
                btn.addClass("btn-disabled").prop("disabled", true).text("Sending...").css({
                    "background-color": "#e9ecef",
                    "color": "#6c757d",
                    "border-color": "#ced4da",
                    "cursor": "wait",
                    "pointer-events": "none"
                });
            }
            
            send_eligibility_email(frm, "To Employee", btn);
        });

        if (btn) {
            const eligibility = parseFloat(frm.doc.eligibility);
            if (!eligibility || eligibility < 500000) {
                btn.addClass("btn-disabled")
                   .css({
                       "background-color": "#e9ecef",
                       "color": "#6c757d",
                       "border-color": "#ced4da",
                       "cursor": "not-allowed",
                       "font-weight": "semibold",
                       "text-transform": "uppercase",
                       "pointer-events": "none"
                   });
            } else {
                btn.removeClass("btn-disabled")
                   .css({
                       "background-color": "#afd1f5",
                       "color": "#004ea1",
                       "border-color": "#007bff",
                       "cursor": "pointer",
                       "font-weight": "semibold",
                       "text-transform": "uppercase",
                       "pointer-events": "auto"
                   });
            }
        }
    }
}

frappe.ui.form.on("ALMS Employee", {
    first_name: function (frm) {
        set_full_name(frm);
    },
    middle_name: function (frm) {
        set_full_name(frm);
    },
    last_name: function (frm) {
        set_full_name(frm);
    }
});

function set_full_name(frm) {
    let first = frm.doc.first_name || "";
    let middle = frm.doc.middle_name || "";
    let last = frm.doc.last_name || "";

    let full_name = [first, middle, last].filter(Boolean).join(" ");

    frm.set_value("full_name", full_name);
}