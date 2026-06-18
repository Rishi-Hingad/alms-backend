// Generic Approval UI Utility for ALMS App
frappe.ui.form.on('*', {
    refresh: function (frm) {
        window.setup_approval_ui(frm);
    }
});

// Explicitly bind to Car Indent Form to override any DocType JS caching issues
frappe.ui.form.on('Car Indent Form', {
    refresh: function (frm) {
        window.setup_approval_ui(frm);
    }
});

window.setup_approval_ui = function (frm) {
    // Always clear old buttons and intervals first to prevent them from sticking around after a status change
    frm.page.wrapper.find('.custom-approve-btn, .custom-reject-btn, .custom-revoke-btn').remove();
    if (frm._approval_btn_interval) clearInterval(frm._approval_btn_interval);
    if (frm._revoke_btn_interval) clearInterval(frm._revoke_btn_interval);

    let doc_status = frm.doc.status;
    let is_pending_approval = (doc_status === 'Pending' || (frm.doc.doctype === 'Invoice Batch' && (doc_status === 'Completed' || doc_status === 'Partially Completed')));
    
    // Removed debug alert

    if (is_pending_approval) {
        frappe.call({
            method: 'alms_app.approval.approval_router.can_approve',
            args: {
                doctype: frm.doc.doctype,
                doc_name: frm.doc.name
            },
            callback: function (r) {
                // Removed debug alert
                
                if (r.message) {
                    // Bypass Frappe's dropdown logic to force two separate buttons
                    frm.page.wrapper.find('.custom-approve-btn, .custom-reject-btn').remove();

                    // Clear any interval that was set by a parallel async call
                    if (frm._approval_btn_interval) {
                        clearInterval(frm._approval_btn_interval);
                        frm._approval_btn_interval = null;
                    }

                    // We are intentionally NOT using frm.add_custom_button to avoid duplicates.
                    // Instead, we strictly rely on the DOM injection below and force the container to be visible.

                    // Frappe's internal async redraws can sometimes wipe out manually injected DOM elements.
                    // We'll use a resilient function to ensure the buttons stay visible.
                    let inject_buttons = () => {
                        let current_is_pending = (frm.doc.status === 'Pending' || (frm.doc.doctype === 'Invoice Batch' && (frm.doc.status === 'Completed' || frm.doc.status === 'Partially Completed')));
                        if (!frm || !frm.doc || !current_is_pending) {
                            if (frm._approval_btn_interval) {
                                clearInterval(frm._approval_btn_interval);
                                frm._approval_btn_interval = null;
                            }
                            frm.page.wrapper.find('.custom-approve-btn, .custom-reject-btn').remove();
                            return;
                        }

                        // Ensure container visibility even if Frappe tries to hide it
                        let container = frm.page.wrapper.find('.page-actions');
                        
                        // Check if buttons are already in the DOM
                        if (frm.page.wrapper.find('.custom-approve-btn').length > 0) {
                            if (container.length > 0 && container.css('display') === 'none') {
                                container.css({'display': 'flex', 'opacity': '1', 'visibility': 'visible'});
                            }
                            return;
                        }

                        let btn_approve = $(`<button class="btn btn-success btn-sm custom-approve-btn" style="color: white; background-color: #28a745; margin-right: 5px;">${__('Approve')}</button>`)
                            .on('click', () => {
                                frappe.confirm(__('Are you sure you want to approve?'), () => {
                                    handle_approval(frm, "Approve");
                                });
                            });

                        let btn_reject = $(`<button class="btn btn-danger btn-sm custom-reject-btn" style="color: white; background-color: #dc3545;">${__('Reject')}</button>`)
                            .on('click', () => {
                                frappe.prompt({
                                    fieldname: 'remarks',
                                    fieldtype: 'Small Text',
                                    label: __('Remarks for Rejection'),
                                    reqd: 1
                                }, function (data) {
                                    handle_approval(frm, "Reject", data.remarks);
                                }, __('Reject Document'), __('Reject'));
                            });

                        let container = frm.page.wrapper.find('.page-actions');
                        if (container.length > 0) {
                            container.css({'display': 'flex', 'opacity': '1', 'visibility': 'visible'});
                            container.prepend(btn_reject).prepend(btn_approve);
                        } else {
                            // Ultimate fallback
                            frm.page.wrapper.find('.title-area').after(btn_approve).after(btn_reject);
                        }
                    };

                    inject_buttons();
                    // Setup interval to repeatedly inject the buttons to fight frappe's async redraws
                    frm._approval_btn_interval = setInterval(inject_buttons, 1000);
                }
            },
            error: function (err) {
                if (frm.doc.doctype === 'Invoice Batch') {
                    frappe.msgprint("Error checking approval API.");
                }
            }
        });

    } else if (frm.doc.status === 'Approved') {
        frappe.call({
            method: 'alms_app.approval.approval_router.can_revoke',
            args: {
                doctype: frm.doc.doctype,
                doc_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.page.wrapper.find('.custom-revoke-btn').remove();

                    if (frm._revoke_btn_interval) {
                        clearInterval(frm._revoke_btn_interval);
                        frm._revoke_btn_interval = null;
                    }

                    let inject_revoke = () => {
                        if (!frm || !frm.doc || frm.doc.status !== 'Approved') {
                            if (frm._revoke_btn_interval) {
                                clearInterval(frm._revoke_btn_interval);
                                frm._revoke_btn_interval = null;
                            }
                            frm.page.wrapper.find('.custom-revoke-btn').remove();
                            return;
                        }

                        let container = frm.page.wrapper.find('.page-actions');

                        if (frm.page.wrapper.find('.custom-revoke-btn').length > 0) {
                            if (container.length > 0 && container.css('display') === 'none') {
                                container.css({'display': 'flex', 'opacity': '1', 'visibility': 'visible'});
                            }
                            return;
                        }

                        let btn_revoke = $(`<button class="btn btn-warning btn-sm custom-revoke-btn" style="color: black; background-color: #ffc107; margin-right: 5px;">${__('Revoke')}</button>`)
                            .on('click', () => {
                                frappe.confirm(__('Are you sure you want to revoke approval?'), () => {
                                    handle_approval(frm, "Revoke");
                                });
                            });

                        let container = frm.page.wrapper.find('.page-actions');
                        if (container.length > 0) {
                            container.css({'display': 'flex', 'opacity': '1', 'visibility': 'visible'});
                            container.prepend(btn_revoke);
                        } else {
                            frm.page.wrapper.find('.title-area').after(btn_revoke);
                        }
                    };

                    inject_revoke();
                    frm._revoke_btn_interval = setInterval(inject_revoke, 1000);
                }
            }
        });
    }

    // Custom Submit Logic based on `is_submitted` field
    if (frm.fields_dict.is_submitted && !frm.doc.is_submitted && frm.doc.docstatus === 0 && !frm.is_new()) {
        frm.page.set_primary_action(__('Submit'), function () {
            frappe.confirm(__('Are you sure you want to submit?'), function () {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: {
                        doctype: frm.doc.doctype,
                        name: frm.doc.name,
                        fieldname: "is_submitted",
                        value: 1
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Document Submitted Successfully.'));
                            frm.reload_doc();
                        }
                    }
                });
            });
        });
    } else {
        // Remove default 'Submit'/'Update' if the form is pending approval
        if (frm.doc.docstatus === 0 && is_pending_approval) {
            frm.page.clear_primary_action();
            frm.page.clear_secondary_action();
        }
    }

    // Call function to render approval trail dynamically
    render_approval_trail(frm);
};

// Handle Approval Action (Approve, Reject, Revoke)
function handle_approval(frm, action, remarks = "") {
    let method_name = "";
    if (action === "Approve") {
        method_name = "alms_app.approval.approval_router.approve_document";
    } else if (action === "Reject") {
        method_name = "alms_app.approval.approval_router.reject_document";
    } else if (action === "Revoke") {
        method_name = "alms_app.approval.approval_router.revoke_document";
    }

    frappe.call({
        method: method_name,
        args: {
            doctype: frm.doc.doctype,
            doc_name: frm.doc.name,
            remarks: remarks
        },
        callback: function (r) {
            if (!r.exc) {
                frappe.msgprint(__(`Document ${action}d Successfully.`));
                frm.reload_doc();
            }
        }
    });
}

// Function to fetch and render the Approval Trail below the form fields
function render_approval_trail(frm) {
    if (frm.is_new()) return;

    frappe.call({
        method: 'alms_app.approval.approval_router.get_approval_trail',
        args: {
            doctype: frm.doc.doctype,
            doc_name: frm.doc.name
        },
        callback: function (r) {
            if (r.message && r.message.length > 0) {
                let html = `<div class="approval-trail-container" style="margin-top: 20px; padding: 15px; border: 1px solid #d1d8dd; border-radius: 4px; background: #f8f9fa;">`;
                html += `<h5><i class="fa fa-history"></i> Approval Trail</h5><ul style="list-style: none; padding-left: 0;">`;

                r.message.forEach(entry => {
                    let icon = "fa-clock-o";
                    let color = "#6c757d"; // gray for pending
                    if (entry.status === "Approved") {
                        icon = "fa-check-circle";
                        color = "#28a745"; // green
                    } else if (entry.status === "Rejected") {
                        icon = "fa-times-circle";
                        color = "#dc3545"; // red
                    } else if (entry.status === "Revoked") {
                        icon = "fa-undo";
                        color = "#ffc107"; // yellow/orange
                    }

                    let action_at = entry.action_at ? frappe.datetime.str_to_user(entry.action_at) : '';
                    let approver = entry.approver_user || entry.next_approver_role || entry.next_approver_team || 'Pending';
                    let remarks = entry.remarks ? ` - <em>"${entry.remarks}"</em>` : '';

                    html += `
                        <li style="margin-bottom: 10px;">
                            <span style="color: ${color}; font-size: 16px;"><i class="fa ${icon}"></i></span>
                            <strong>${entry.action || 'Pending'}</strong> by <strong>${approver}</strong> 
                            ${action_at ? `<small class="text-muted">on ${action_at}</small>` : ''}
                            ${remarks}
                        </li>
                    `;
                });

                html += `</ul></div>`;

                let form_wrapper = frm.page.wrapper.find('.form-message').parent();
                form_wrapper.find('.approval-trail-container').remove(); // remove old one
                form_wrapper.append(html);
            } else {
                frm.page.wrapper.find('.approval-trail-container').remove();
            }
        }
    });
}