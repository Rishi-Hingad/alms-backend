window.open_invoice_dialog = function () {
    let lease_id = null;
    let agreement_start = null;
    let agreement_end = null;

    let extra_attachments = [];

    const d = new frappe.ui.Dialog({
        title: 'Add Invoice for Lease',
        fields: [
            {
                label: 'Lease ID',
                fieldname: 'lease_id',
                fieldtype: 'Link',
                options: 'Lease Management',
                reqd: 1,
                change: function () {
                    lease_id = d.get_value('lease_id');
                    if (lease_id) {
                        load_lease_info(lease_id, d);
                        toggle_invoice_fields(true);
                    }
                    else{
                        toggle_invoice_fields(false);
                    }
                }
            },
            { fieldtype: 'Section Break' },
            {
                label: 'Agreement Start Date',
                fieldname: 'start_date',
                fieldtype: 'Date',
                read_only: 1
            },
            {
                fieldtype: 'Column Break'
            },
            {
                label: 'Agreement End Date',
                fieldname: 'end_date',
                fieldtype: 'Date',
                read_only: 1
            },
            { fieldtype: 'Section Break' },
            {
                label: 'Previous Invoices',
                fieldname: 'invoice_html',
                fieldtype: 'HTML'
            },
            { fieldtype: 'Section Break' },
            {
                label: 'Month',
                fieldname: 'month',
                fieldtype: 'Select',
                options: 'January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember',
                reqd: 1
            },
            {
                label: 'From Date',
                fieldname: 'from_date',
                fieldtype: 'Date',
                reqd: 1
            },
            {
                label: 'To Date',
                fieldname: 'to_date',
                fieldtype: 'Date',
                reqd: 1
            },
            {
                label: 'Amount',
                fieldname: 'amount',
                fieldtype: 'Float',
                reqd: 1
            },
            {
                label: 'Invoice Attachment',
                fieldname: 'invoice_attachment',
                fieldtype: 'Attach',
                reqd: 1
            },
            {
                label: "Attachments",
                fieldname: "manage_attachments",
                fieldtype: "Button",
            },
            {
                label: 'With Tax',
                fieldname: 'with_tax',
                fieldtype: 'Check'
            },
            {
                label: 'Tax (%)',
                fieldname: 'tax',
                fieldtype: 'Percent'
            },
            // {
            //     label: 'Payment Status',
            //     fieldname: 'payment_status',
            //     fieldtype: 'Select',
            //     options: 'Unpaid\nPaid',
            //     default: 'Unpaid'
            // }
        ],
        primary_action_label: 'Add Invoice',
        primary_action(values) {
            if (!lease_id) return;

            // ✅ Date validation
            const from_date = frappe.datetime.str_to_obj(values.from_date);
            const to_date = frappe.datetime.str_to_obj(values.to_date);
            const start_date = frappe.datetime.str_to_obj(agreement_start);
            const end_date = frappe.datetime.str_to_obj(agreement_end);

            if (from_date < start_date || to_date > end_date || from_date > to_date) {
                frappe.msgprint(__('From and To Dates must be within Agreement Start and End Date'));
                return;
            }

            // ✅ Proceed with invoice save
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Lease Management",
                    name: lease_id
                },
                callback: function(r) {
                    if (r.message) {
                        const doc = r.message;
                        doc.invoice_details = doc.invoice_details || [];

                        const current_length = (doc.invoice_details || []).length;
                        const idx = current_length + 1;

                        const formatDate = (dateStr) => {
                            const d = frappe.datetime.str_to_obj(dateStr);
                            return `${("0" + d.getDate()).slice(-2)}-${("0" + (d.getMonth() + 1)).slice(-2)}-${d.getFullYear()}`;
                        };

                        const from_formatted = formatDate(values.from_date);
                        const to_formatted = formatDate(values.to_date);

                        const custom_row_id = `row-${idx}-${from_formatted}-to-${to_formatted}`;

                        const row = {
                            month: values.month,
                            from_date: values.from_date,
                            to_date: values.to_date,
                            amount: values.amount,
                            invoice_attachment: values.invoice_attachment,
                            with_tax: values.with_tax ? 1 : 0,
                            tax: values.tax || 0,
                            // payment_status: values.payment_status,
                            custom_row_id: custom_row_id
                        };

                        doc.invoice_details.push(row);

                        doc.invoice_attachments = doc.invoice_attachments || [];

                        extra_attachments.forEach(file => {
                            const attachment_row = {
                                file: file.file_url,
                                file_docname: "", // Optionally set if available
                                invoice_row: custom_row_id,
                                uploaded_by: frappe.session.user,
                                uploaded_on: frappe.datetime.now_datetime()
                            };

                            if (!doc.invoice_attachments) {
                                doc.invoice_attachments = [];
                            }
                            doc.invoice_attachments.push(attachment_row);
                        });
                        console.log("Extra attachments to save:", extra_attachments);


                        frappe.call({
                            method: "frappe.client.set_value",
                            args: {
                                doctype: "Lease Management",
                                name: lease_id,
                                fieldname: {
                                    invoice_details: doc.invoice_details,
                                    invoice_attachments:doc.invoice_attachments
                                }
                            },
                            callback: function(save_r) {
                                if (!save_r.exc) {
                                    frappe.msgprint("Invoice added successfully.");
                                    d.hide();
                                }
                            }
                        });
                    }
                }
            });
        }
    });

    function toggle_invoice_fields(visible) {
        const fields_to_toggle = [
            'start_date', 'end_date', 'invoice_html',
            'month', 'from_date', 'to_date', 'amount',
            'invoice_attachment', 'manage_attachments',
            'with_tax', 'tax'
        ];

        fields_to_toggle.forEach(fieldname => {
            if (visible) {
                d.get_field(fieldname).$wrapper.show();
            } else {
                d.get_field(fieldname).$wrapper.hide();
            }
        });
    }

    d.show();
    toggle_invoice_fields(false);

    d.fields_dict.manage_attachments.input.onclick = () => {
        const upload_dialog = new frappe.ui.Dialog({
            title: "Upload Additional Attachments",
            fields: [
                {
                    label: "File(s)",
                    fieldname: "files",
                    fieldtype: "Attach",
                    reqd: 1
                }
            ],
            primary_action_label: "Attach",
            primary_action(values) {
                if (values.files) {
                    extra_attachments.push({
                        file_url: values.files,
                        name: frappe.utils.get_random(10) // fake name to differentiate
                    });
                    frappe.msgprint("Attachment added.");
                    upload_dialog.hide();
                }
            }
        });

        upload_dialog.show();
    };

    // Modified loader to store start/end dates in outer variables
    function load_lease_info(lease_id, dialog) {
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Lease Management",
                name: lease_id
            },
            callback: function(r) {
                const doc = r.message;
                agreement_start = doc.agreement_start_date;
                agreement_end = doc.agreement_end_date;

                dialog.set_value('start_date', agreement_start);
                dialog.set_value('end_date', agreement_end);

                let html = `
                <div style="margin-bottom: 10px;">
                    <strong style="font-size: 14px;">Previous Invoices</strong>
                </div>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th>From</th>
                            <th>To</th>
                            <th>Amount</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>`;
                
                const invoices = doc.invoice_details || [];

                if (invoices.length === 0) {
                    html += `<tr>
                        <td colspan="5" class="text-center text-muted">No Invoice Details Added Yet.</td>
                    </tr>`;
                } else {
                    invoices.forEach(inv => {
                        html += `<tr>
                            <td>${inv.month}</td>
                            <td>${inv.from_date}</td>
                            <td>${inv.to_date}</td>
                            <td>${inv.amount}</td>
                            <td>${inv.payment_status || 'Unpaid'}</td>
                        </tr>`;
                    });
                }

                html += '</tbody></table>';

                dialog.fields_dict.invoice_html.$wrapper.html(html);
            }
        });
    } 
};