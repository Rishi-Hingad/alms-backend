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
    },
    agreement_end_date: function(frm) {
        validate_dates_and_set_lease_period(frm);
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

        // if (frappe.user.has_role("Vendor")){
        //     frm.set_df_property('escalation','hidden',true);
        // }
        // else if(user==="Administrator" || frappe.user.has_role("System Manager")){
        //     frm.set_df_property('escalation','hidden',false);
        // }
        // else if(frappe.user.has_role("Accounts")){
        //     frm.set_df_property('escalation','hidden',false);
        // }
        // else{
        //     frm.set_df_property('escalation','hidden',false);
        // }

        // frm.refresh_field('escalation');
    },
    onload(frm) {
        frm.report_counter = 0;
    },
    refresh: function (frm) { 
        // if (frappe.user.has_role("Vendor")){
        //     frm.set_df_property('escalation','hidden',true);
        // }
        // else if(user==="Administrator" || frappe.user.has_role("System Manager")){
        //     frm.set_df_property('escalation','hidden',false);
        // }
        // else if(frappe.user.has_role("Accounts")){
        //     frm.set_df_property('escalation','hidden',false);
        // }
        // else{
        //     frm.set_df_property('escalation','hidden',false);
        // }

        // frm.refresh_field('escalation');

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
            row.wrapper.css({
                'background-color':'#f59090ff'
            });
        }
        else{
            row.wrapper.css({
                'background-color':''
            });
        }
    });
}