// frappe.ui.form.on("Escalation Rule", {
//     escalation_param(frm, cdt, cdn) {
//         console.log("escalation_param changed");
//         const row = locals[cdt][cdn];
//         handle_escalation_param(frm, row);
//     },

//     escalation_value(frm, cdt, cdn) {
//         const row = locals[cdt][cdn];
//         validate_escalation_value(frm, row);
//     }
// });

// function handle_escalation_param(frm, row) {
//     const grid = frm.fields_dict.escalation_rules.grid;

//     frappe.model.set_value(row.doctype, row.name, "escalation_value", null);
//     frappe.model.set_value(row.doctype, row.name, "escalation_uom", null);
//     frappe.model.set_value(row.doctype, row.name, "currency", null);

//     if (row.escalation_param === "Time") {
//         grid.toggle_display("escalation_uom", true);
//         grid.toggle_display("currency", false);

//         grid.toggle_reqd("escalation_uom", true);
//         grid.toggle_reqd("currency", false);
//     }

//     else if (row.escalation_param === "Amount") {
//         grid.toggle_display("escalation_uom", false);
//         grid.toggle_display("currency", true);

//         grid.toggle_reqd("currency", true);
//         grid.toggle_reqd("escalation_uom", false);
//     }

//     else {
//         grid.toggle_display("escalation_uom", false);
//         grid.toggle_display("currency", false);
//         grid.toggle_reqd("escalation_uom", false);
//         grid.toggle_reqd("currency", false);
//     }
// }

// function validate_escalation_value(frm, row) {
//     if (!row.escalation_value) return;

//     if (row.escalation_param === "Time" && row.escalation_value <= 0) {
//         frappe.msgprint("Time must be greater than zero");
//         frappe.model.set_value(row.doctype, row.name, "escalation_value", null);
//     }

//     if (row.escalation_param === "Amount" && row.escalation_value < 0) {
//         frappe.msgprint("Amount cannot be negative");
//         frappe.model.set_value(row.doctype, row.name, "escalation_value", null);
//     }
// }
