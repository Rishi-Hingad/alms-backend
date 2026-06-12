window.setup_approval_ui = function (frm) {
    console.log('[Approval UI] setup_approval_ui called for:', frm.doc.doctype, frm.doc.name);
    console.log('[Approval UI] Current doc status:', frm.doc.status);

    // Always clear old buttons and intervals first to prevent them from sticking around after a status change
    frm.page.wrapper.find('.custom-approve-btn, .custom-reject-btn, .custom-revoke-btn').remove();
    if (frm._approval_btn_interval) clearInterval(frm._approval_btn_interval);
    if (frm._revoke_btn_interval) clearInterval(frm._revoke_btn_interval);

    if (frm.doc.status === 'Pending') {
        console.log('[Approval UI] Form is Pending. Calling can_approve API...');
        frappe.call({
            method: 'alms_app.approval.approval_router.can_approve',
            args: {
                doctype: frm.doc.doctype,
                doc_name: frm.doc.name
            },
            callback: function (r) {
                console.log('[Approval UI] can_approve API response:', r);
                if (r.message) {
                    console.log('[Approval UI] Adding Approve and Reject buttons...');
                    // Bypass Frappe's dropdown logic to force two separate buttons
                    frm.page.wrapper.find('.custom-approve-btn, .custom-reject-btn').remove();

                    // Frappe's internal async redraws can sometimes wipe out manually injected DOM elements.
                    // We'll use a resilient function to ensure the buttons stay visible.
                    let inject_buttons = () => {
                        if (!frm || !frm.doc || frm.doc.status !== 'Pending') {
                            if (frm._approval_btn_interval) clearInterval(frm._approval_btn_interval);
                            return;
                        }

                        // Check if buttons are already in the DOM
                        if (frm.page.wrapper.find('.custom-approve-btn').length > 0) return;

                        let btn_approve = $(`<button class="btn btn-success btn-sm custom-approve-btn" style="color: white; background-color: #28a745; margin-right: 5px;">${__('Approve')}</button>`)
                            .click(() => handle_approval_action(frm, 'Approve'));

                        let btn_reject = $(`<button class="btn btn-danger btn-sm custom-reject-btn" style="color: white; background-color: #dc3545; margin-right: 5px;">${__('Reject')}</button>`)
                            .click(() => handle_approval_action(frm, 'Reject'));

                        // Prepend directly to page-actions so they don't get hidden inside standard-actions
                        let container = frm.page.wrapper.find('.page-actions');
                        if (container.length > 0) {
                            container.prepend(btn_reject).prepend(btn_approve);
                        } else {
                            // Ultimate fallback
                            frm.page.wrapper.find('.title-area').after(btn_approve).after(btn_reject);
                        }
                    };

                    // Inject immediately
                    inject_buttons();

                    // Re-check periodically to handle Frappe's aggressive UI redrawing
                    if (frm._approval_btn_interval) {
                        clearInterval(frm._approval_btn_interval);
                    }
                    frm._approval_btn_interval = setInterval(inject_buttons, 1000);
                }
                
                // Always check if user can revoke, regardless of whether they can currently approve
                console.log('[Approval UI] Checking if user can revoke.');
                frappe.call({
                    method: 'alms_app.approval.approval_router.has_previously_approved',
                    args: { doctype: frm.doc.doctype, doc_name: frm.doc.name },
                    callback: function (r_revoke) {
                        if (r_revoke.message) {
                            let inject_revoke = () => {
                                if (!frm || !frm.doc || frm.doc.status !== 'Pending') {
                                    if (frm._revoke_btn_interval) clearInterval(frm._revoke_btn_interval);
                                    return;
                                }
                                if (frm.page.wrapper.find('.custom-revoke-btn').length > 0) return;

                                let btn_revoke = $(`<button class="btn btn-danger btn-sm custom-revoke-btn" style="color: white; background-color: #dc3545; margin-right: 5px;">${__('Revoke & Reject')}</button>`)
                                    .click(() => handle_revoke_action(frm));

                                let container = frm.page.wrapper.find('.page-actions');
                                if (container.length > 0) {
                                    container.prepend(btn_revoke);
                                } else {
                                    frm.page.wrapper.find('.title-area').after(btn_revoke);
                                }
                            };
                            inject_revoke();
                            if (frm._revoke_btn_interval) clearInterval(frm._revoke_btn_interval);
                            frm._revoke_btn_interval = setInterval(inject_revoke, 1000);
                        }
                    }
                });
            },
            error: function (err) {
                console.error('[Approval UI] Error calling can_approve:', err);
            }
        });
    } else if (frm.doc.status === 'Approved' || frm.doc.status === 'Rejected') {
        console.log('[Approval UI] Form is ' + frm.doc.status + '. Checking if user can revoke.');
        
        frappe.call({
            method: 'alms_app.approval.approval_router.has_previously_approved',
            args: { doctype: frm.doc.doctype, doc_name: frm.doc.name },
            callback: function (r_revoke) {
                if (r_revoke.message || frappe.session.user === 'Administrator') {
                    let inject_revoke = () => {
                        if (!frm || !frm.doc) {
                            if (frm._revoke_btn_interval) clearInterval(frm._revoke_btn_interval);
                            return;
                        }
                        if (frm.page.wrapper.find('.custom-revoke-btn').length > 0) return;

                        let btn_revoke = $(`<button class="btn btn-danger btn-sm custom-revoke-btn" style="color: white; background-color: #dc3545; margin-right: 5px;">${__('Revoke & Reject')}</button>`)
                            .click(() => handle_revoke_action(frm));

                        let container = frm.page.wrapper.find('.page-actions');
                        if (container.length > 0) {
                            container.prepend(btn_revoke);
                        } else {
                            frm.page.wrapper.find('.title-area').after(btn_revoke);
                        }
                    };
                    inject_revoke();
                    if (frm._revoke_btn_interval) clearInterval(frm._revoke_btn_interval);
                    frm._revoke_btn_interval = setInterval(inject_revoke, 1000);
                }
            }
        });
    } else {
        console.log('[Approval UI] Form is ' + frm.doc.status + '. Skipping button render.');
    }

    // Render approval trail if the field exists
    console.log('[Approval UI] Checking if we should render approval trail...');
    console.log('[Approval UI] frm.fields_dict.approval_trail_html exists?', !!frm.fields_dict.approval_trail_html);
    console.log('[Approval UI] frm.doc.status is:', frm.doc.status);

    if (frm.fields_dict.approval_trail_html && (frm.doc.status === 'Pending' || frm.doc.status === 'Approved' || frm.doc.status === 'Rejected')) {
        console.log('[Approval UI] Conditions met. Calling render_approval_trail...');
        render_approval_trail(frm);
    } else {
        console.warn('[Approval UI] Conditions NOT met for rendering timeline. Timeline will be skipped.');
    }

    // Custom Submit Logic based on `is_submitted` field
    if (frm.fields_dict.is_submitted && !frm.doc.is_submitted && frm.doc.docstatus === 0 && !frm.is_new()) {
        frm.add_custom_button(__('Submit Document'), function () {
            frappe.confirm(__('Are you sure you want to submit this document for approval?'), () => {
                frm.set_value('is_submitted', 1);
                frm.save();
            });
        }).addClass('btn-primary');
    }
};

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

function handle_approval_action(frm, action) {
    let title = action === 'Approve' ? __('Approve Document') : __('Reject Document');
    frappe.prompt([
        {
            fieldname: 'remarks',
            fieldtype: 'Data',
            label: __('Remarks'),
            reqd: action === 'Reject'
        }
    ], function (values) {
        frappe.call({
            method: 'alms_app.approval.approval_router.process_approval_action',
            args: {
                doctype: frm.doc.doctype,
                doc_name: frm.doc.name,
                action: action,
                remarks: values.remarks || ''
            },
            freeze: true,
            freeze_message: __('Processing...'),
            callback: function (r) {
                if (!r.exc) {
                    frappe.show_alert({ message: r.message.message, indicator: r.message.status === 'success' ? 'green' : 'red' });
                    frm.reload_doc();
                }
            }
        });
    }, title, __('Submit'));
}

function handle_revoke_action(frm) {
    frappe.prompt([
        {
            fieldname: 'remarks',
            fieldtype: 'Data',
            label: __('Reason for Revocation & Rejection'),
            reqd: true
        }
    ], function (values) {
        frappe.confirm(__('Are you sure you want to revoke your previous approval and reject this request? This will restart the approval process from the beginning.'), () => {
            frappe.call({
                method: 'alms_app.approval.approval_router.revoke_and_reject_approval',
                args: {
                    doctype: frm.doc.doctype,
                    doc_name: frm.doc.name,
                    remarks: values.remarks || ''
                },
                freeze: true,
                freeze_message: __('Revoking...'),
                callback: function (r) {
                    if (!r.exc) {
                        frappe.show_alert({ message: r.message.message || __('Revoked Successfully'), indicator: 'green' });
                        frm.reload_doc();
                    }
                }
            });
        });
    }, __('Revoke & Reject'), __('Confirm'));
}

function render_approval_trail(frm) {
    console.log('[Approval UI] render_approval_trail called. Making API request...');
    frappe.call({
        method: 'alms_app.approval.approval_utils.get_approval_trail',
        args: {
            doctype: frm.doc.doctype,
            docname: frm.doc.name
        },
        callback: function (r) {
            console.log('[Approval UI] get_approval_trail API Response:', r);
            if (r.message && r.message.status === 'success') {
                let data = r.message.data;
                console.log('[Approval UI] Calling build_timeline_html with data:', data);
                let html = build_timeline_html(frm, data);
                $(frm.fields_dict.approval_trail_html.wrapper).html(html);
            } else {
                console.warn('[Approval UI] API did not return success. Message:', r.message);
            }
        },
        error: function (err) {
            console.error('[Approval UI] get_approval_trail API Error:', err);
        }
    });
}

function build_timeline_html(frm, trail_data) {
    if (!trail_data || !trail_data.length) return '';

    let html = `
        <style>
            .approval-timeline-container {
                width: 100%;
                overflow-x: auto;
                padding: 15px 0;
            }

            .approval-timeline {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                align-items: flex-start;
                gap: 20px;
                position: relative;
                min-width: max-content;
                padding-top: 25px;
            }

            .approval-timeline::before {
                content: "";
                position: absolute;
                top: 36px;
                left: 0;
                right: 0;
                height: 2px;
                background: #e0e0e0;
                z-index: 0;
            }

            .approval-stage {
                width: 220px;
                min-width: 220px;
                flex: 0 0 220px;
                position: relative;
                text-align: center;
                z-index: 1;
            }

            .approval-node {
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: #cacaca;
                border: 2px solid #fff;
                box-shadow: 0 0 0 2px #e0e0e0;
                margin: 0 auto 15px auto;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
            }

            .approval-card {
                padding: 12px;
                border-radius: 6px;
                background: var(--control-bg, #f8f9fa);
                border: 1px solid var(--border-color, #e2e8f0);
            }
        </style>

        <div class="approval-timeline-container">
            <div class="approval-timeline">
    `;

    let status_banner = '';

    if (frm.doc.status === 'Approved') {
        status_banner = `
                <div style="
                    background:#d4edda;
                    color:#155724;
                    border:1px solid #c3e6cb;
                    padding:12px;
                    border-radius:8px;
                    margin-bottom:15px;
                    font-weight:600;
                    text-align:center;
                ">
                    <i class="fa fa-check-circle"></i>
                    Document Fully Approved
                </div>
            `;
    }

    trail_data.forEach(function (item) {

        let node_bg = '#cacaca';
        let node_icon = 'fa-circle';
        let node_shadow = '#e0e0e0';

        if (item.variant === 'success') {
            node_bg = '#28a745';
            node_icon = 'fa-check';
            node_shadow = '#28a74555';
        }
        else if (item.variant === 'danger') {
            node_bg = '#dc3545';
            node_icon = 'fa-times';
            node_shadow = '#dc354555';
        }
        else if (item.variant === 'pending') {
            node_bg = '#ffc107';
            node_icon = 'fa-clock-o';
            node_shadow = '#ffc10755';
        }
        else if (item.variant === 'upcoming') {
            node_bg = '#dee2e6';
            node_icon = 'fa-circle-o';
            node_shadow = '#dee2e655';
        }

        let badge_style =
            'background-color:#007bff;color:#fff;margin-bottom:8px;display:inline-block;';

        if (item.variant === 'success') {
            badge_style = `background:#28a745; color:white; font-weight:600; padding:6px 12px;border-radius:20px; display:inline-block; margin-bottom:8px;`;
        }
        else if (item.variant === 'danger') {
            badge_style = `background:#dc3545; color:white; font-weight:600; padding:6px 12px border-radius:20px; display:inline-block; margin-bottom:8px;`;
        }
        else if (item.variant === 'pending') {
            badge_style = `background:#ffc107; color:white; font-weight:600; padding:6px 12px border-radius:20px; display:inline-block; margin-bottom:8px;`;
        }
        else if (item.variant === 'upcoming') {
            badge_style = `background:#e9ecef; color:white; font-weight:600; padding:6px 12px border-radius:20px; display:inline-block; margin-bottom:8px;`;
        }
        else if (item.variant === 'info') {
            badge_style = 'background-color:#17a2b8;color:#fff;margin-bottom:8px;display:inline-block;';
        }

        let approvers_html = '';

        if (item.variant === 'pending' || item.variant === 'upcoming') {
            if (item.role) {
                approvers_html = `<b>Role: ${item.role}</b>`;
            } else if (item.team) {
                approvers_html = `<b>Team: ${item.team}</b>`;
            } else if (item.approver && item.approver.length) {
                approvers_html = item.approver
                    .map(a => `<b style="display:block;">${a.full_name}</b>`)
                    .join('');
            }
        } else {
            if (item.approver && item.approver.length) {
                let role_team_text = '';
                if (item.role) {
                    role_team_text = `<span style="font-size: 0.85em; color: var(--text-muted, #6c757d); display:block;">(${item.role})</span>`;
                } else if (item.team) {
                    role_team_text = `<span style="font-size: 0.85em; color: var(--text-muted, #6c757d); display:block;">(${item.team})</span>`;
                }
                approvers_html = item.approver
                    .map(a => `<b style="display:block;">${a.full_name}</b>${role_team_text}`)
                    .join('');
            } else if (item.role) {
                approvers_html = `<b>Role: ${item.role}</b>`;
            } else if (item.team) {
                approvers_html = `<b>Team: ${item.team}</b>`;
            }
        }

        let action_line = item.action_line
            ? `<div class="text-muted small" style="margin-top:5px;">${item.action_line}</div>`
            : '';

        let card_style = '';

        if (item.variant === 'success') {
            card_style = `
                border:1px solid #28a745;
                background:#f0fff4;
            `;
        }
        else if (item.variant === 'danger') {
            card_style = `
                border:1px solid #dc3545;
                background:#fff5f5;
            `;
        }
        else if (item.variant === 'pending') {
            card_style = `
                border:1px solid #ffc107;
                background:#fffdf0;
            `;
        }

        html += `
            <div class="approval-stage">
                <div class="approval-node"
                    style="
                        background:${node_bg};
                        box-shadow:0 0 0 4px ${node_shadow};
                    ">
                    <i class="fa ${node_icon}" style="font-size:11px;"></i>
                </div>

                <div class="approval-card" style="${card_style}">
                    <span class="badge" style="${badge_style}">
                        ${item.label}
                    </span>

                    <div style="font-size:0.9em;line-height:1.4;">
                        ${approvers_html}
                    </div>

                    ${action_line}
                </div>
            </div>
        `;
    });

    html += `
            </div>
        </div>
    `;

    html = status_banner + html;

    return html;
}