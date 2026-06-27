/* =============
TimeLine
===============*/
frappe.ui.form.on("Car Quotation", {
    refresh(frm) {

        frm.add_custom_button("View Timeline", async () => {

            const root = frm.doc.root_quotation || frm.doc.name;

            const res = await frappe.call({
                method: "lease_app.crms.doctype.car_quotation.car_quotation.get_quotation_timeline",
                args: { root_id: root }
            });

            renderTimeline(res.message);
        });
    }
});

function renderTimeline(data) {

    let html = `
        <div style="padding:20px;">
            <div style="border-left:3px solid #3b82f6; margin-left:10px;">
    `;

    data.forEach(q => {

        html += `
            <div style="margin:20px 0; padding-left:20px; position:relative;">
                
                <div style="
                    position:absolute;
                    left:-11px;
                    top:5px;
                    width:16px;
                    height:16px;
                    background:#3b82f6;
                    border-radius:50%;
                "></div>

                <div style="
                    background:#f8fafc;
                    padding:10px 15px;
                    border-radius:8px;
                    box-shadow:0 2px 6px rgba(0,0,0,0.05);
                ">
                    <b>${q.name}</b> (v${q.version_number})<br>
                    Vendor: ${q.finance_company}<br>
                    Status: ${q.status}<br>
                    <small>${frappe.datetime.str_to_user(q.creation)}</small>
                </div>
            </div>
        `;
    });

    html += "</div></div>";

    const d = new frappe.ui.Dialog({
        title: "Quotation Timeline",
        size: "large",
        fields: [{ fieldtype: "HTML", fieldname: "timeline" }]
    });

    d.show();
    d.fields_dict.timeline.$wrapper.html(html);
}

/* ================================
 FILE UPLOAD
================================ */
function uploadfile(frm) {

    if (frm.doc.finance_team_status !== "Approved") {

        // ✅ Revised Email → backend call (NO send_email)
        frm.add_custom_button('Send Revised Quot Email', function () {

            frappe.prompt(
                {
                    label: 'Remark',
                    fieldname: 'remark',
                    fieldtype: 'Small Text',
                    reqd: 0
                },
                async function (values) {

                    frm.set_value('revised_remark', values.remark || "");
                    await frm.save();

                    await frappe.call({
                        method: "lease_app.api.emailsService.email_sender",
                        args: {
                            name: frm.doc.employee_details,
                            email_send_to: "FinanceHead To Quotation Company",
                            payload: {
                                email_phase: "Revised",
                                quotation_id: frm.doc.name,
                                email_send_to: [frm.doc.finance_company],
                                remark: values.remark || ""
                            }
                        }
                    });

                    frappe.msgprint("Revised email sent");

                },
                __('Add Remark'),
                __('Send Email')
            );

        });
    }
}


/* ================================
 SET VALUES FROM FILE
================================ */
function setValuesInField(frm, data) {

    const fields = [
        "finance_company", "accessory", "gst_and_cess",
        "employee_details", "discount_excluding_gst", "insurance",
        "location", "base_price_less_discounts", "fleet_management_repairs_and_tyres",
        "kms", "total_discount", "24x7_assist",
        "variant", "ex_showroom_amount_net_of_discount", "pickup_and_drop",
        "quote", "registration_charges",
        "interest_rate", "residual_value_percent", "std_relief_car_non_accdt",
        "tenure", "financed_amount", "gst_on_fms",
        "base_price_excluding_gst", "total_emi",
        "gst", "emi_financing", "status",
        "ex_showroom_amount", "finance_emi_road_tax"
    ];

    fields.forEach(f => {
        if (data[f] !== undefined) {
            frm.set_value(f, data[f]);
        }
    });
}


/* ================================
 STATUS BUTTONS (CLEAN VERSION)
================================ */
function updateStatus(frm) {
    frm.clear_custom_buttons();
}


/* ================================
 FIELD ACCESS CONTROL
================================ */
function toggleFieldStatus(frm) {
    // Rely on generic Frappe field permissions or standard logic.
}


/* ================================
 FORM EVENTS
================================ */
frappe.ui.form.on('Car Quotation', {

    onload(frm) {
        // One-time setup only
        frm.set_df_property("status", "read_only", true);
    },

    refresh(frm) {
        frm.set_df_property("status", "read_only", true);

        frm.clear_custom_buttons();
        
        if (typeof setup_approval_ui === "function") {
            setup_approval_ui(frm);
        }

        uploadfile(frm);
        addDeductionButton(frm);
    }

});


/* ================================
 EMI CALCULATION
================================ */
frappe.ui.form.on("Car Quotation", {

    total_emi(frm) {

        let total_emi = flt(frm.doc.total_emi);

        if (!total_emi) {
            frm.set_value("quarterly_payment", 0);
            frm.set_value("interim_payment", 0);
            return;
        }

        let quarterly_payment = Math.round(total_emi * 3);
        let interim_payment = Math.round((quarterly_payment * 39) / 90);

        frm.set_value("quarterly_payment", quarterly_payment);
        frm.set_value("interim_payment", interim_payment);
    }

});


/* ================================
 DEDUCTION BUTTON
================================ */

function addDeductionButton(frm) {

    let role = "";
    if (frappe.user_roles.includes("Administrator")) role = "Administrator";
    else if (frappe.user_roles.includes("Finance Head")) role = "Finance Head";
    else if (frappe.user_roles.includes("Finance Team") || frappe.user_roles.includes("Finance")) role = "Finance";

    console.log("User Role:", role);
    const isFinanceUser = ["Finance", "Administrator"].includes(role);

            // Show button after Finance Team approval
            if (
                isFinanceUser &&
                frm.doc.status === "Approved"
            ) {

                frm.add_custom_button("Generate Deduction", () => {
                    openDeductionDialog(frm, role);
                });
            }
}

function openDeductionDialog(frm, role) {

    frappe.call({
        method: "lease_app.crms.doctype.car_quotation.car_quotation.preview_deduction",
        args: {
            quotation_id: frm.doc.name
        },
        callback(r) {

            if (!r.message) return;

            const isFinanceHeadApproved = frm.doc.status === "Approved";

            let d = new frappe.ui.Dialog({
                title: "Quarterly Payment Preview",
                fields: [
                    {
                        label: "Company Quarterly Payment",
                        fieldname: "quarterly_payment",
                        fieldtype: "Currency",
                        default: r.message.quarterly_payment,
                        read_only: 1
                    },
                    {
                        label: "Employee Quarterly Payment",
                        fieldname: "employee_quarterly_payment",
                        fieldtype: "Currency",
                        default: r.message.employee_quarterly_payment,
                        read_only: 1
                    }
                ],
                primary_action_label: "Generate",
                primary_action() {

                    if (!isFinanceHeadApproved) {
                        frappe.msgprint("Finance Head approval required.");
                        return;
                    }

                    frappe.call({
                        method: "lease_app.crms.doctype.car_quotation.car_quotation.create_deduction_doc",
                        args: {
                            quotation_id: frm.doc.name
                        },
                        callback(res) {

                            frappe.msgprint("Deduction created");

                            frappe.set_route(
                                "Form",
                                "Company and Employee Deduction",
                                res.message
                            );
                        }
                    });

                    d.hide();
                }
            });

            d.show();

            if (!isFinanceHeadApproved) {
                d.get_primary_btn()
                    .prop("disabled", true)
                    .text("Waiting for Finance Head Approval");
            }
        }
    });
}