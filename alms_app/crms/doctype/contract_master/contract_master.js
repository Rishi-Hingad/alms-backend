frappe.ui.form.on("Contract Master", {

    refresh: function(frm) {

        if (!frm.is_new()) {

            frm.add_custom_button("Renew Contract", function() {

                // Validate existing data
                if (!frm.doc.contract_start_date || !frm.doc.contract_end_date) {
                    frappe.msgprint("No contract data found to renew.");
                    return;
                }

                // Add entry in child table
                let row = frm.add_child("old_contract_details");

                row.old_contract_start_date = frm.doc.contract_start_date;
                row.old_contract_end_date = frm.doc.contract_end_date;
                row.old_no_of_installments = frm.doc.no_of_installments;
                row.old_additional_cost = frm.doc.additional_cost;
                row.old_contract_agreement = frm.doc.upload_contract;
                row.contact_number = frm.doc.contract_number;

                frm.refresh_field("old_contract_details");

                // Clear main contract fields
                frm.set_value("contract_start_date", null);
                frm.set_value("contract_end_date", null);
                frm.set_value("additional_cost", null);
                frm.set_value("no_of_installments", 0);
                frm.set_value("upload_contract", null);
                frm.set_value("contract_number", null);

                frm.clear_table("installment_date");
                frm.refresh_field("installment_date");

                frappe.msgprint({
                    title: "Renewed",
                    indicator: "green",
                    message: "Previous contract archived. Enter new contract details."
                });

            });
        }
    },

    contract_start_date: function(frm) {
        frm.trigger("calculate_installments");
    },

    contract_end_date: function(frm) {
        frm.trigger("calculate_installments");
    },

    calculate_installments: function(frm) {

        if (!frm.doc.contract_start_date || !frm.doc.contract_end_date) {
            return;
        }

        let start_date = frappe.datetime.str_to_obj(frm.doc.contract_start_date);
        let end_date = frappe.datetime.str_to_obj(frm.doc.contract_end_date);

        if (start_date > end_date) {
            frappe.msgprint("Contract End Date cannot be before Start Date");
            frm.clear_table("installment_date");
            frm.refresh_field("installment_date");
            frm.set_value("no_of_installments", 0);
            return;
        }

        // Clear existing rows
        frm.clear_table("installment_date");

        let installment_count = 0;
        let current_start = new Date(start_date);

        while (current_start <= end_date) {

            let current_end = new Date(current_start);
            current_end.setMonth(current_end.getMonth() + 3);
            current_end.setDate(current_end.getDate() - 1);

            if (current_end > end_date) {
                current_end = new Date(end_date);
            }

            let row = frm.add_child("installment_date");
            row.installment_start_date = frappe.datetime.obj_to_str(current_start);
            row.installment_end_date = frappe.datetime.obj_to_str(current_end);

            installment_count++;

            // Move to next quarter
            current_start.setMonth(current_start.getMonth() + 3);
        }

        frm.refresh_field("installment_date");
        frm.set_value("no_of_installments", installment_count);
    }
});
