// Copyright (c) 2025, Shradha_Siddhi and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Lease Management", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Escalation',{
    escalation_type:function(frm,cdt,cdn){
        auto_set_start_end_date_escalation(frm,cdt,cdn);
    },
    start_date: function(frm, cdt, cdn) {
        validate_escalation_dates(frm, cdt, cdn);
    },
    end_date: function(frm, cdt, cdn) {
        validate_escalation_dates(frm, cdt, cdn);
    }
});
frappe.ui.form.on('Invoice Documents',{
    from_date: function(frm, cdt, cdn) {
        validate_from_to_dates(frm, cdt, cdn);
    },
    to_date: function(frm, cdt, cdn) {
        validate_from_to_dates(frm, cdt, cdn);
    },

     manage_attachments: function(frm, cdt, cdn) {
        if (frm.is_new()) {
        frappe.msgprint(__('Save the document before adding attachments.'));
        return;
        }

        const row = locals[cdt][cdn];

        // gather current attachments for this invoice-row
        const att = (frm.doc.invoice_attachments || []).filter(a => a.invoice_row === row.custom_row_id);

        // Dialog to show attachments and upload new ones
        const dialog = new frappe.ui.Dialog({
        // title: `Attachments for ${row.month || row.from_date || row.name}`,
        title: `Attachments for ${row.from_date} to ${row.to_date}`,
        fields: [
            { fieldtype: 'HTML', fieldname: 'attachment_list' }
        ],
        primary_action_label: 'Upload file(s)',
        primary_action: function() {
            // Use built-in upload dialog (multiple files)
        //     frappe.ui.get_upload_dialog({
        //     multi: true,
        //     // attach_to_doctype & docname can help Frappe link the uploaded File to parent,
        //     // but if parent is saved we can attach to parent doctype/docname for convenience:
        //     doctype: frm.doctype,
        //     docname: frm.doc.name,
        //     callback: (files) => {
        //         // files is array of file objects returned by upload dialog
        //         files.forEach(f => {
        //         const new_child = frm.add_child('invoice_attachments');
        //         new_child.file = f.file_url || f.file_name || f.url;
        //         new_child.file_docname = f.name; // this is the File docname
        //         new_child.invoice_row = row.name;
        //         new_child.uploaded_by = frappe.session.user;
        //         new_child.uploaded_on = frappe.datetime.now_datetime();
        //         });
        //         frm.refresh_field('invoice_attachments');
        //         dialog.hide();
        //     }
        //     });
        // }
        // });
            new frappe.ui.FileUploader({
            allow_multiple: 1,
            doctype: frm.doctype,
            docname: frm.doc.name,
            folder: 'Home/Attachments',
            on_success: (file) => {
                // file is a single File doc
                const new_child = frm.add_child('invoice_attachments');
                new_child.file = file.file_url;
                new_child.file_docname = file.name;
                new_child.invoice_row = row.custom_row_id;
                new_child.uploaded_by = frappe.session.user;
                new_child.uploaded_on = frappe.datetime.now_datetime();

                frm.refresh_field('invoice_attachments');
                dialog.hide();
            },
            onerror: (err) => {
                frappe.msgprint(__('Upload failed: {0}', [err]));
            }
            });
        }
        });

        dialog.show();

        frappe.call({
            method: "lms.lease_management_system.doctype.lease_management.lease_management.get_invoice_attachments",
            args: {
                filters: {
                    parent: frm.doc.name,
                    parenttype: frm.doctype,
                    invoice_row: row.custom_row_id
                }
            },
            callback: function(r) {
                // console.log("Fetched attachments:", r.message);
                const $wrapper = dialog.fields_dict.attachment_list.$wrapper.empty();
                const attachments = r.message || [];

                if (!attachments.length) {
                    $wrapper.html('<div class="text-muted">No attachments yet</div>');
                    return;
                }

                // const $list = $('<ul class="list-unstyled"></ul>');
                // attachments.forEach(a => {
                //     // const link = `<a href="${a.file}" target="_blank">${frappe.utils.get_basename(a.file)}</a>`;
                //     // Use JS split instead of frappe.utils.get_basename
                //     const filename = a.file.split('/').pop();
                //     const link = `<a href="${a.file}" target="_blank">${filename}</a>`;
                //     const meta = `<span class="text-muted small"> (by ${a.uploaded_by}, ${frappe.datetime.str_to_user(a.uploaded_on)})</span>`;
                //     const remove_button = `<a class="text-muted" style="margin-left:10px;cursor:pointer;" data-name="${a.name}">Delete</a>`;
                //     $list.append(`<li>${link} ${meta} ${remove_button}</li>`);
                // });
                // $wrapper.append($list);

                // Create a table with bootstrap classes
                const $table = $(`
                    <table class="table table-bordered table-sm">
                        <thead>
                            <tr>
                                <th>File</th>
                                <th>Uploaded By</th>
                                <th>Uploaded On</th>
                                <th style="width: 80px;">Action</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                `);

                attachments.forEach(a => {
                    const filename = a.file.split('/').pop();
                    const row = `
                        <tr>
                            <td><a href="${a.file}" target="_blank">${filename}</a></td>
                            <td>${a.uploaded_by}</td>
                            <td>${frappe.datetime.str_to_user(a.uploaded_on)}</td>
                            <td>
                                <a class="text-danger" style="cursor:pointer;" data-name="${a.name}">
                                    Delete
                                </a>
                            </td>
                        </tr>
                    `;
                    $table.find("tbody").append(row);
                });

                $wrapper.append($table);

                // Hook delete clicks
                $wrapper.on('click', 'a[data-name]', function() {
                    const name = $(this).attr('data-name');
                    frappe.confirm(__('Delete this attachment?'), () => {
                        frappe.call({
                            method: 'lms.lease_management_system.doctype.lease_management.lease_management.delete_invoice_attachment',
                            args: {
                                parent_doctype: frm.doctype,
                                parent_name: frm.doc.name,
                                attachment_name: name,
                                delete_file: false
                            },
                            callback: function(r) {
                                if (r.message === 'ok') {
                                    frm.reload_doc(); // reload whole doc so UI is in sync
                                    dialog.hide();
                                }
                            }
                        });
                    });
                });
            }
        });

        // // Render existing attachments inside the dialog
        // const $wrapper = dialog.fields_dict.attachment_list.$wrapper.empty();

        // if (!att.length) {
        // $wrapper.html('<div class="text-muted">No attachments yet</div>');
        // return;
        // }

        // const $list = $('<ul class="list-unstyled"></ul>');
        // att.forEach(a => {
        // // show link + small delete action
        // const link = `<a href="${a.file}" target="_blank">${frappe.utils.get_basename(a.file)}</a>`;
        // const remove_button = `<a class="text-muted" style="margin-left:10px;cursor:pointer;" data-name="${a.custom_row_id}">Delete</a>`;
        // $list.append(`<li>${link} ${remove_button}</li>`);
        // });
        // $wrapper.append($list);

        // // hook delete clicks
        // $wrapper.on('click', 'a[data-name]', function() {
        // const name = $(this).attr('data-name');
        // frappe.confirm(
        //     __('Delete this attachment?'),
        //     () => {
        //     frappe.call({
        //         method: 'lms.lease_management_system.doctype.lease_management.lease_management.delete_invoice_attachment',
        //         args: {
        //         parent_doctype: frm.doctype,
        //         parent_name: frm.doc.name,
        //         attachment_name: name,
        //         delete_file: false
        //         },
        //         callback: function(r) {
        //         if (r.message === 'ok') {
        //             // remove local child row
        //             frm.doc.invoice_attachments = (frm.doc.invoice_attachments || []).filter(x => x.name !== name);
        //             frm.refresh_field('invoice_attachments');
        //             dialog.hide();
        //             frm.reload_doc(); // optional: refresh the document to get latest state from server
        //         }
        //         }
        //     });
        //     }
        // );
        // });
    }



    // attachments: function(frm, cdt, cdn) {
    // const row = locals[cdt][cdn];

    // // Fetch existing attachment data if already added (optional enhancement)
    // let existing_attachments = row._invoice_attachments || [];

    // const dialog = new frappe.ui.Dialog({
    //     title: 'Invoice Attachments',
    //     size: 'large',
    //     fields: [
    //         {
    //         fieldname: 'invoice_attachments',
    //         label: 'Attachments',
    //         fieldtype: 'Table',
    //         cannot_add_rows: false,
    //         options:'Invoice Attachments',
    //         // in_place_edit: false,
    //         fields: [
    //             {
    //             fieldname: 'attachment',
    //             fieldtype: 'Attach',
    //             label: 'Attachment',
    //             reqd: 1
    //             }
    //         ],
    //         data: existing_attachments
    //         }
    //     ],
    //     primary_action_label: 'Save',
    //     primary_action(values) {
    //         // Save data temporarily in the row (in-memory only)
    //         frappe.model.set_value(cdt, cdn, 'multiple_invoice_attachments', values.invoice_attachments);

    //         // Optionally, show a message or count
    //         frappe.msgprint(`${values.invoice_attachments.length} attachment(s) saved for this invoice.`);
    //         dialog.hide();
    //     }
    //     });

    //     dialog.show();
    // }
    
    // refresh:function(frm,cdt,cdn){
    //     let row=locals[cdt][cdn];
    //     console.log(row.is_mismatch);
    //     if (row.is_mismatch){
    //         frappe.utils.show_alert({
    //             message:`Mismatch found in Invoice Details for month ${row.month} and from date ${row.from_date}`,
    //             indicator:'red'
    //         });
    //     }
    // },
    // invoice_details_add:function(frm){
    //     frm.fields_dict['invoice_details'].grid.refresh();
    // }
});

frappe.ui.form.on("Lease Management", {

    agreement_start_date: function(frm) {
        validate_dates_and_set_lease_period(frm);
        // set_agreement_status(frm);
    },
    agreement_end_date: function(frm) {
        validate_dates_and_set_lease_period(frm);
        // set_agreement_status(frm);
    },
    // lease_period:function(frm){
    //     if(frm.doc.lease_period!='' && frm.doc.lease_period=='Short Term (Less Than 12 Months)'){
    //         frm.set_df_property('escalation', 'reqd', 0);
    //     }
    //     else if(frm.doc.lease_period!='' && frm.doc.lease_period=='Long Term (Greater Than 12 Months)'){
    //         frm.set_df_property('escalation', 'reqd', 1);
    //     }
    //     else{
    //         frm.set_df_property('escalation', 'reqd', 0);
    //     }
    // },
    security_deposit:function(frm){
        if(frm.doc.security_deposit=='Paid'){
            frm.set_df_property('security_deposit_amount','reqd',1);
        }
    },
    onload_post_render(frm){
        if(frm.doc.invoice_details && frm.doc.invoice_details.length >0 && (frappe.user.has_role("Accounts") || frappe.user.has_role("System Manager"))){
            highlight_mismatched_rows(frm);
        }
    },
    onload(frm) {
        frm.report_counter = 0;
        // set_agreement_status(frm);
    },
    refresh: function (frm) { 
        // set_agreement_status(frm);
        if(frm.doc.invoice_details && frm.doc.invoice_details.length >0 && (frappe.user.has_role("Accounts") || frappe.user.has_role("System Manager"))){
            highlight_mismatched_rows(frm);
        }

        if(frappe.user.has_role("Vendor")){
            frm.fields_dict.invoice_details.grid.df.read_only=0;
            frm.fields_dict.invoice_details.grid.refresh();
        }
        if(!(frm.doc.discounting_rate)&&frm.is_new()){
            frappe.db.get_list('Discounting Rate', {
                limit: 1,
                order_by: 'creation asc', 
                fields: ['name', 'discounting_rate'] 
            }).then(records => {
                if (records.length > 0) {
                    const first_record = records[0];
                    frm.set_value('discounting_rate', first_record.discounting_rate);
                } else {
                    frappe.msgprint('No records found.');
                }
            });
        }
        
        frm.set_query("property_description", function () {
        return {
            filters: {
            vendor_code: frm.doc.vendor
            }
        }});
        
        if(!frm.is_new()){
            if(frappe.user.has_role("Accounts") || frappe.user.has_role("System Manager")){
                frm.add_custom_button(__('Generate Report'), function() {
                    frm.report_counter = (frm.report_counter || 0) + 1;
                    frappe.call({
                        method: 'lms.lease_management_system.doctype.lease_management.lease_management.generate_report',
                        args: {
                            docname: frm.doc.name,
                            cnt:frm.report_counter
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                // frappe.msgprint(__(r.message));
                                // console.log(r.message)
                                let file_url = r.message.file_url;
                                window.open(file_url);
                            }else {
                                frappe.msgprint(__('Failed to generate report.'));
                            }
                        }
                    });
                        // frappe.msgprint(__('Button clicked!'));
                });

                frm.add_custom_button('Go to Report', function() {
                    let lname = frm.doc.name;
                    if (frm.doc.calculation_rate_type=="Daily Rate" && frm.doc.lease_period=="Long Term (Greater Than 12 Months)"){
                        frappe.set_route('query-report', 'Lease Report', {
                            'docname': lname
                        });
                    } 
                    else if (frm.doc.calculation_rate_type=="Daily Rate" && frm.doc.lease_period=="Short Term (Less Than 12 Months)"){
                        frappe.set_route('query-report', 'Lease Report (Without Escalation)', {
                            'docname': lname
                        });
                    }
                    else if (frm.doc.calculation_rate_type=="Monthly Rate" && frm.doc.lease_period=="Long Term (Greater Than 12 Months)"){
                        frappe.set_route('query-report', 'Lease Report Monthly (With Escalation)', {
                            'docname': lname
                        });
                    } 
                    else if (frm.doc.calculation_rate_type=="Monthly Rate" && frm.doc.lease_period=="Short Term (Less Than 12 Months)"){
                        frappe.set_route('query-report', 'Lease Report Monthly (Without Escalation)', {
                            'docname': lname
                        });
                    }
                });
            }
            
        }
        
    },
    validate: function(frm) {
        // if(frm.doc.lease_period === "Long Term (Greater Than 12 Months)") {
        //     if(!frm.doc.escalation || frm.doc.escalation.length === 0) {
        //         frappe.msgprint(__('Escalation table is mandatory for Long Term leases.'));
        //         frappe.validated = false;  // prevent save
        //     }
        // }

        let escalation = frm.doc.escalation || [];
        if (escalation.length === 0) return;

        let consecutivePerAnnum = 0;
        let consecutivePerAnnumandFixed = 0;

        for (let row of escalation) {
            if (row.escalation_type === "Per Annum") {
                consecutivePerAnnum += 1;
                if (consecutivePerAnnum >= 2) {
                    frappe.throw("You cannot have 2 or more consecutive 'Per Annum' values in escalation type");
                }
            }
            else if (row.escalation_type === "Per Annum and Fixed Amount") {
                consecutivePerAnnumandFixed += 1;
                if (consecutivePerAnnumandFixed >= 2) {
                    frappe.throw("You cannot have 2 or more consecutive 'Per Annum and Fixed Amount' values in escalation type");
                }
            }
            else {
                consecutivePerAnnum = 0;  // Reset 
                consecutivePerAnnumandFixed = 0;  
            }
        }
        
        frm.doc.escalation.forEach(row => {
            // if(row.escalation_type === 'Per Annum' && !row.rate) {
            //     frappe.msgprint(`Rate is mandatory for Per Annum escalation at row ${row.idx}`);
            //     frappe.validated = false;
            //     return false;
            // }
            if(row.escalation_type === 'Based On Dates') {
                if(!row.start_date || !row.end_date) {
                    frappe.msgprint(`Start Date, End Date and Monthly Rent are mandatory for Based On Dates escalation at row ${row.idx}`);
                    frappe.validated = false;
                    return false;
                }
            }
            // if(row.escalation_type === 'Per Annum and Fixed Amount' && (!row.rate || !row.fixed_amount)) {
            //     frappe.msgprint(`Rate and Fixed Amount are mandatory for Per Annum and Fixed Amount escalation at row ${row.idx}`);
            //     frappe.validated = false;
            //     return false;
            // }
        });
    }
});

function set_agreement_status(frm){
    const start_date = frm.doc.agreement_start_date;
    const end_date = frm.doc.agreement_end_date;
    if(start_date && end_date) {
        if(end_date <= start_date) {
            frappe.msgprint(__('Agreement End Date must be greater than Agreement Start Date.'));
            frm.set_value('agreement_end_date', null);
            return;
        }

        let new_status=null;
        if (end_date < frappe.datetime.get_today()){
            new_status='Agreement Expired';
        }
        else{
            new_status='Active';
        }
        if (frm.doc.status !== new_status){
            frm.set_value('status', new_status);
            frm.save()
                .then(() => {
                    frm.reload_doc();
                });
        }
    }
}

function validate_dates_and_set_lease_period(frm){
    const start_date = frm.doc.agreement_start_date;
    const end_date = frm.doc.agreement_end_date;
    if(start_date && end_date) {
        if(end_date <= start_date) {
            frappe.msgprint(__('Agreement End Date must be greater than Agreement Start Date.'));
            frm.set_value('agreement_end_date', null);
            return;
        }

        // Calculate difference in months between dates
        const start = frappe.datetime.str_to_obj(start_date);
        const end = frappe.datetime.str_to_obj(end_date);

        let months_diff = (end.getFullYear() - start.getFullYear()) * 12;
        months_diff -= start.getMonth();
        months_diff += end.getMonth();

        if(months_diff > 12) {
            frm.set_value('lease_period', 'Long Term (Greater Than 12 Months)');
        } else {
            frm.set_value('lease_period', 'Short Term (Less Than 12 Months)');
        }

        if (end_date < frappe.datetime.get_today()){
            frm.set_value('status', 'Agreement Expired');
        }
        else{
            frm.set_value('status', 'Active');
        }
        

    }
}

function auto_set_start_end_date_escalation(frm,cdt,cdn){
    const row = frappe.get_doc(cdt, cdn);
    const agreement_start = frm.doc.agreement_start_date;
    const agreement_end = frm.doc.agreement_end_date;
    frappe.model.set_value(cdt, cdn, 'start_date', agreement_start);
    frappe.model.set_value(cdt, cdn, 'end_date', agreement_end);
    // if(row.escalation_type == 'Based On Dates'){
    //     //set start and end date to agreement start and end date
    //     frappe.model.set_value(cdt, cdn, 'start_date', agreement_start);
    //     frappe.model.set_value(cdt, cdn, 'end_date', agreement_end);
    // }
}

function validate_escalation_dates(frm, cdt, cdn){
    const row = frappe.get_doc(cdt, cdn);
    const agreement_start = frm.doc.agreement_start_date;
    const agreement_end = frm.doc.agreement_end_date;

    if(!agreement_start || !agreement_end) {
        frappe.msgprint(__('Please set Agreement Start Date and Agreement End Date first.'));
        return;
    }

    if(row.start_date && row.end_date) {
        // Check escalation start/end dates are inside agreement range
        if(row.start_date < agreement_start || row.end_date > agreement_end) {
            frappe.msgprint(__('Escalation Start and End Dates must be within Agreement Start and Agreement End Dates.'));
            frappe.model.set_value(cdt, cdn, 'start_date', null);
            frappe.model.set_value(cdt, cdn, 'end_date', null);
            return;
        }

        // Check escalation end date is greater than start date
        if(row.end_date <= row.start_date) {
            frappe.msgprint(__('Escalation End Date must be greater than Escalation Start Date.'));
            frappe.model.set_value(cdt, cdn, 'end_date', null);
        }
    }
}

function validate_from_to_dates(frm, cdt, cdn){
    const row = frappe.get_doc(cdt, cdn);
    const agreement_start = frm.doc.agreement_start_date;
    const agreement_end = frm.doc.agreement_end_date;

    if(!agreement_start || !agreement_end) {
        frappe.msgprint(__('Please set Agreement Start Date and Agreement End Date first'));
        return;
    }

    if(row.from_date && row.to_date) {
        if(row.from_date < agreement_start || row.to_date > agreement_end) {
            frappe.msgprint(__('Invoice From and To Dates must be within Agreement Start and Agreement End Dates'));
            frappe.model.set_value(cdt, cdn, 'from_date', null);
            frappe.model.set_value(cdt, cdn, 'to_date', null);
            return;
        }

        if(row.to_date <= row.from_date) {
            frappe.msgprint(__('Invoice To Date must be greater than Invoice From Date'));
            frappe.model.set_value(cdt, cdn, 'to_date', null);
        }
    }
}

function highlight_mismatched_rows(frm){
    const grid=frm.fields_dict['invoice_details'].grid;
    grid.grid_rows.forEach(row => {
        const row_data=row.doc;
        if (row.wrapper  && row_data.is_mismatch==1){
            // console.log(row_data.from_date);
            // console.log(row_data.to_date);
            // console.log(row_data.tax);
            // console.log(row_data.with_tax);
            row.wrapper.css({
                // 'background-color':'#f59090ff'
                'background-color':'#f8d7da'
            });
        }
        else{
            row.wrapper.css({
                'background-color':''
            });
        }
    });
}