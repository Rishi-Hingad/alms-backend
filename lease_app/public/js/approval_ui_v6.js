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
    // Clear old native custom buttons if they exist
    try {
        frm.remove_custom_button(__('Approve'));
        frm.remove_custom_button(__('Reject'));
        frm.remove_custom_button(__('Revoke Last Approval'));
    } catch(e) {}
    
    // Also remove any old raw HTML buttons just in case
    frm.page.wrapper.find('.custom-approve-btn, .custom-reject-btn, .custom-revoke-btn').remove();

    let doc_status = frm.doc.status;
    let is_pending_approval = (doc_status === 'Pending' || (frm.doc.doctype === 'Invoice Batch' && (doc_status === 'Completed' || doc_status === 'Partially Completed')));
    console.log(`[Approval UI] Checking ${frm.doc.doctype} (${frm.doc.name}). Status: ${doc_status}, is_pending_approval: ${is_pending_approval}`);
    
    // Removed debug alert

    if (is_pending_approval) {
        frappe.call({
            method: 'lease_app.approval.approval_router.can_approve',
            args: {
                doctype: frm.doc.doctype,
                doc_name: frm.doc.name
            },
            callback: function (r) {
                console.log("[Approval UI] can_approve returned:", r.message);
                
                if (r.message) {
                    // Use native Frappe button injection to guarantee visibility
                    frm.remove_custom_button(__('Approve'));
                    frm.remove_custom_button(__('Reject'));

                    let approve_btn = frm.add_custom_button(__('Approve'), () => {
                        frappe.prompt({
                            fieldname: 'remarks',
                            fieldtype: 'Small Text',
                            label: __('Remarks for Approval (Optional)')
                        }, function (data) {
                            handle_approval(frm, "Approve", data.remarks);
                        }, __('Approve Document'), __('Approve'));
                    });
                    approve_btn.removeClass('btn-default').addClass('btn-success').css({
                        'color': 'white', 
                        'background-color': '#28a745', 
                        'border-color': '#28a745',
                        'margin-right': '5px'
                    });

                    let reject_btn = frm.add_custom_button(__('Reject'), () => {
                        frappe.prompt({
                            fieldname: 'remarks',
                            fieldtype: 'Small Text',
                            label: __('Remarks for Rejection'),
                            reqd: 1
                        }, function (data) {
                            handle_approval(frm, "Reject", data.remarks);
                        }, __('Reject Document'), __('Reject'));
                    });
                    reject_btn.removeClass('btn-default').addClass('btn-danger').css({
                        'color': 'white', 
                        'background-color': '#dc3545',
                        'border-color': '#dc3545'
                    });
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
            method: 'lease_app.approval.approval_router.can_revoke',
            args: {
                doctype: frm.doc.doctype,
                doc_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.remove_custom_button(__('Revoke Last Approval'));
                    let btn_revoke = frm.add_custom_button(__('Revoke Last Approval'), () => {
                        frappe.confirm(__('Are you sure you want to revoke the last approval? This will roll back the document to Pending state.'), () => {
                            frappe.call({
                                method: 'lease_app.approval.approval_router.revoke_last_approval',
                                args: {
                                    doctype: frm.doc.doctype,
                                    doc_name: frm.doc.name,
                                    reason: 'Revoked by admin'
                                },
                                callback: function (r) {
                                    if (!r.exc && r.message && r.message.status === 'success') {
                                        frappe.show_alert({message: r.message.message, indicator: 'green'});
                                        frm.reload_doc();
                                    } else {
                                        frappe.msgprint({title: __('Error'), message: r.message ? r.message.message : __('Failed to revoke approval'), indicator: 'red'});
                                    }
                                }
                            });
                        });
                    });
                    btn_revoke.removeClass('btn-default').addClass('btn-warning').css({
                        'color': 'black', 
                        'background-color': '#ffc107',
                        'border-color': '#ffc107',
                        'margin-right': '5px'
                    });
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
    frappe.call({
        method: "lease_app.approval.approval_router.process_approval_action",
        args: {
            doctype: frm.doc.doctype,
            doc_name: frm.doc.name,
            action: action,
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
        method: 'lease_app.approval.approval_router.get_approval_trail',
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

                let target_wrapper = frm.layout.wrapper || frm.page.wrapper.find('.form-page');
                if (target_wrapper.length === 0) target_wrapper = frm.page.wrapper;
                
                target_wrapper.find('.approval-trail-container').remove(); // remove old one
                target_wrapper.append(html);
            } else {
                let target_wrapper = frm.layout.wrapper || frm.page.wrapper.find('.form-page');
                if (target_wrapper.length === 0) target_wrapper = frm.page.wrapper;
                target_wrapper.find('.approval-trail-container').remove();
            }
        }
    });
}