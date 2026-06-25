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
            method: 'alms_app.approval.approval_router.can_approve',
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
            method: 'alms_app.approval.approval_router.can_revoke',
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
                                method: 'alms_app.approval.approval_router.revoke_last_approval',
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
        if (frm.doc.docstatus === 0 && is_pending_approval && !frm.is_new()) {
            frm.page.clear_primary_action();
            frm.page.clear_secondary_action();
            
            // Forcefully remove in case Frappe core form.js runs late and re-adds the native Submit button
            setTimeout(() => {
                frm.page.clear_primary_action();
                frm.page.clear_secondary_action();
            }, 100);
            setTimeout(() => {
                frm.page.clear_primary_action();
                frm.page.clear_secondary_action();
            }, 500);
        }
    }

    // Call function to render approval trail dynamically
    render_approval_trail(frm);
};

// Handle Approval Action (Approve, Reject, Revoke)
function handle_approval(frm, action, remarks = "") {
    frappe.call({
        method: "alms_app.approval.approval_router.process_approval_action",
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
        method: 'alms_app.approval.approval_router.get_approval_trail',
        args: {
            doctype: frm.doc.doctype,
            doc_name: frm.doc.name
        },
        callback: function (r) {
            if (r.message && r.message.length > 0) {
                let html = `
                <div class="approval-trail-container" style="margin-top: 30px; margin-bottom: 30px;">
                    <div class="form-section">
                        <div class="section-head" style="margin-bottom: 20px; border-bottom: 1px solid #d1d8dd; padding-bottom: 10px;">
                            <h4 style="font-weight: 600; color: #1f272e; display: flex; align-items: center; gap: 8px; margin: 0;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-muted"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>
                                Approval Routing History
                            </h4>
                        </div>
                        <div class="timeline" style="position: relative; padding-left: 24px; border-left: 2px solid #e2e8f0; margin-left: 12px; font-family: inherit;">
                `;

                r.message.forEach((entry, index) => {
                    let icon = "fa-clock-o";
                    let bg_color = "#64748b"; // slate-500 for pending
                    
                    if (entry.status === "Approved") {
                        icon = "fa-check";
                        bg_color = "#10b981"; // emerald-500
                    } else if (entry.status === "Rejected") {
                        icon = "fa-times";
                        bg_color = "#ef4444"; // red-500
                    } else if (entry.status === "Revoked") {
                        icon = "fa-undo";
                        bg_color = "#f59e0b"; // amber-500
                    }

                    let action_at = entry.action_at ? frappe.datetime.str_to_user(entry.action_at) : '';
                    let approver = entry.approver_user || entry.next_approver_role || entry.next_approver_team || 'Pending';
                    
                    // Determine if this is the last item
                    let is_last = (index === r.message.length - 1);
                    let margin_bottom = is_last ? "0" : "24px";

                    html += `
                        <div class="timeline-item" style="position: relative; margin-bottom: ${margin_bottom};">
                            <!-- Timeline Badge -->
                            <div class="timeline-badge" style="position: absolute; left: -36px; top: 2px; width: 24px; height: 24px; border-radius: 50%; background: ${bg_color}; color: white; display: flex; align-items: center; justify-content: center; font-size: 11px; border: 3px solid white; box-shadow: 0 0 0 1px ${bg_color}; z-index: 1;">
                                <i class="fa ${icon}"></i>
                            </div>
                            
                            <!-- Timeline Content Card -->
                            <div class="timeline-content" style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin-left: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: box-shadow 0.2s ease, transform 0.2s ease;" onmouseover="this.style.boxShadow='0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)'; this.style.transform='translateY(-1px)';" onmouseout="this.style.boxShadow='0 1px 2px rgba(0,0,0,0.05)'; this.style.transform='translateY(0)';">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                                    <div style="font-weight: 600; color: #0f172a; font-size: 14px; display: flex; align-items: center; gap: 6px;">
                                        <span style="color: ${bg_color};">${entry.action || 'Pending'}</span>
                                        <span style="color: #94a3b8; font-weight: 400; font-size: 13px;">by</span>
                                        <span>${approver}</span>
                                    </div>
                                    ${action_at ? `<div style="font-size: 12px; color: #64748b; font-weight: 500; background: #f1f5f9; padding: 2px 8px; border-radius: 12px;">${action_at}</div>` : ''}
                                </div>
                                
                                ${entry.remarks ? `
                                <div style="margin-top: 12px; padding: 10px 14px; background: #f8fafc; border-radius: 6px; border-left: 3px solid ${bg_color}; font-size: 13px; color: #334155; line-height: 1.5;">
                                    <strong>Remarks:</strong> ${entry.remarks}
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                });

                html += `</div></div></div>`;

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