frappe.listview_settings["Car Quotation"] = {

    onload: async function (listview) {

        let role = "";
        if (frappe.user_roles.includes("Administrator")) role = "administrator";
        else if (frappe.user_roles.includes("Finance Head")) role = "finance head";
        else if (frappe.user_roles.includes("Finance Team") || frappe.user_roles.includes("Finance")) role = "finance";

        if (["finance", "administrator", "finance head"].includes(role)) {

            listview.page.add_inner_button("Compare Quotations", async () => {

                frappe.prompt(
                    [
                        {
                            fieldname: "purchase_form",
                            label: "Select Approved Purchase Form",
                            fieldtype: "Link",
                            options: "Purchase Form",
                            get_query: () => ({
                                query: "alms_app.crms.doctype.car_quotation.car_quotation.get_available_purchase_forms"
                            }),
                            reqd: 1
                        }
                    ],
                    async (values) => {

                        const purchaseForm = values.purchase_form;

                        const res = await frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Car Quotation",
                                filters: {
                                    employee_details: purchaseForm
                                },
                                fields: [
                                    "name", "finance_company", "status", "location",
                                    "total_kms", "interest_rate", "ex_showroom_amount",
                                    "accessories", "total_discount",
                                    "ex_showroom_amount_net_of_discount",
                                    "registration_charges", "financed_amount", "total_emi", "variant",
                                    "finance_team_status", "finance_head_status", "finance_team_remarks", "finance_head_remarks"
                                ]
                            }
                        });

                        const data = res.message || [];

                        if (!data.length) {
                            frappe.msgprint("No quotations found.");
                            return;
                        }

                        openQuotationDialog(data, role, purchaseForm, listview);
                    },
                    "Select Purchase Form",
                    "Proceed"
                );
            });
        }
    }
};


/* ================================
 HELPERS
================================ */
const flt = v => parseFloat(v) || 0;

function rankVendors(data) {
    return data.sort((a, b) =>
        (flt(a.total_emi) - flt(b.total_emi)) ||
        (flt(a.interest_rate) - flt(b.interest_rate)) ||
        (flt(a.financed_amount) - flt(b.financed_amount))
    );
}

function formatCurrency(val) {
    return val ? "₹ " + Number(val).toLocaleString("en-IN") : "-";
}

function formatPercent(val) {
    return val ? `${val} %` : "-";
}


/* ================================
 MAIN DIALOG
================================ */
function openQuotationDialog(data, role, purchaseForm, listview) {

    let rankedData = rankVendors([...data]);
    let best = rankedData[0];

    rankedData.forEach(d => {
        d._isTop =
            flt(d.total_emi) === flt(best.total_emi) &&
            flt(d.interest_rate) === flt(best.interest_rate) &&
            flt(d.financed_amount) === flt(best.financed_amount);
    });

    let fields = [
        { label: "Quotation ID", key: "name" },
        { label: "Car Variant", key: "variant" },
        { label: "Location", key: "location" },
        { label: "Total KMs", key: "total_kms" },
        { label: "Interest Rate", key: "interest_rate" },
        { label: "Ex-Showroom", key: "ex_showroom_amount" },
        { label: "Discount", key: "total_discount" },
        { label: "Accessories", key: "accessories" },
        { label: "Net Amount", key: "ex_showroom_amount_net_of_discount" },
        { label: "Registration", key: "registration_charges" },
        { label: "Financed Amount", key: "financed_amount" },
        { label: "Total EMI", key: "total_emi" },
        { label: "Finance Team Status", key: "finance_team_status" },
        { label: "Finance Team Remarks", key: "finance_team_remarks" },
        { label: "Finance Head Status", key: "finance_head_status" },
        { label: "Finance Head Remarks", key: "finance_head_remarks" }
    ];

    /* ================================
    BUILD HTML TABLE
    ================================= */
    let html = `
        <div style="overflow-x:auto;">
        <table class="table table-bordered" 
            style="min-width:${Math.max(800, rankedData.length * 260)}px; 
                text-align:center; 
                border-collapse:collapse;
                table-layout:fixed;">

            <thead>
                <tr style="background:#f1f5f9;">
                    <!-- FIELD COLUMN -->
                    <th style="
                        min-width:180px;
                        max-width:180px;
                        width:180px;
                        background:#e2e8f0;
                        position:sticky;
                        left:0;
                        z-index:2;
                        text-align:left;
                        padding-left:10px;
                    ">
                        Field
                    </th>

                    <!-- VENDOR HEADERS -->
                    ${rankedData.map((q, i) => `
                        <th style="
                            background:${q._isTop ? '#d1fae5' : '#f8fafc'};
                            min-width:180px;
                            font-weight:600;
                        ">
                            <div style="font-size:12px; color:#64748b;">#${i + 1}</div>
                            <div>${q.finance_company}</div>
                        </th>
                    `).join("")}
                </tr>
            </thead>

            <tbody>
                ${fields.map(f => `
                    <tr>
                        <!-- FIELD COLUMN -->
                        <td style="
                            background:#f8fafc;
                            font-weight:600;
                            text-align:left;
                            padding-left:10px;
                            position:sticky;
                            left:0;
                            z-index:1;
                            width:180px;
                            max-width:180px;
                            white-space:nowrap;
                        ">
                            ${f.label}
                        </td>

                        ${rankedData.map(q => {
        let v = q[f.key];

        if (f.key === "interest_rate") v = formatPercent(v);
        else if (f.key === "total_kms") v = v ? Number(v).toLocaleString("en-IN") : "-";
        else if ([
            "ex_showroom_amount", "total_discount", "accessories",
            "ex_showroom_amount_net_of_discount", "registration_charges",
            "financed_amount", "total_emi"
        ].includes(f.key)) {
            v = formatCurrency(v);
        }

        return `
                                <td style="
                                    background:${q._isTop ? '#ecfdf5' : 'white'};
                                    ${q._isTop ? 'font-weight:600;' : ''}
                                ">
                                    ${v || "-"}
                                </td>
                            `;
    }).join("")}
                    </tr>
                `).join("")}

                <!-- ACTION ROW -->
                <tr>
                    <td style="
                        background:#e2e8f0;
                        font-weight:700;
                        position:sticky;
                        left:0;
                        z-index:1;
                        padding-left:10px;
                    ">
                        Action
                    </td>

                    ${rankedData.map(q => `
                        <td style="background:${q._isTop ? '#ecfdf5' : ''}">
                            <div style="display:flex; justify-content:center; gap:6px;">
                                <button class="btn btn-success btn-xs approve" data-id="${q.name}">✔</button>
                                <button class="btn btn-danger btn-xs reject" data-id="${q.name}">✖</button>
                                <button class="btn btn-primary btn-xs send-revised" data-id="${q.name}" title="Send Revised Request">
                                    ✉
                                </button>
                            </div>
                        </td>
                    `).join("")}
                </tr>

            </tbody>
        </table>
        </div>
        `;

    /* ================================
    DIALOG
    ================================= */
    const d = new frappe.ui.Dialog({
        title: "Compare Quotations",
        size: "extra-large",
        fields: [
            { fieldtype: "HTML", fieldname: "html" }
        ],
        primary_action_label: "Export to Excel",
        primary_action: () => exportToExcel(rankedData)
    });

    d.show();
    d.fields_dict.html.$wrapper.html(html);


    /* ================================
    APPROVE / REJECT
    ================================= */
    d.$wrapper.on("click", ".approve, .reject", async function () {

        const btn = $(this);
        const id = btn.data("id");
        const action = btn.hasClass("approve") ? "Approved" : "Rejected";

        if (btn.prop("disabled")) return;
        btn.prop("disabled", true);

        try {
            const { remarks } = await new Promise(resolve => {
                frappe.prompt(
                    [{ fieldname: "remarks", label: "Remarks", fieldtype: "Data", reqd: 1 }],
                    resolve
                );
            });

            await frappe.call({
                method: "alms_app.crms.doctype.car_quotation.car_quotation.process_workflow",
                args: {
                    quotation_id: id,
                    action: action,
                    remarks: remarks
                }
            });

            frappe.msgprint(`${action} successful`);
            d.hide();
            if (listview) listview.refresh();

        } catch (e) {
            console.error(e);
        } finally {
            btn.prop("disabled", false);
        }
    });

    d.$wrapper.on("click", ".send-revised", async function () {

        const id = $(this).data("id");
        const vendor = rankedData.find(q => q.name === id)?.finance_company || "";

        // Optional prompt (recommended)
        const { remarks } = await new Promise(resolve => {
            frappe.prompt(
                [
                    {
                        fieldname: "remarks",
                        label: `Revised Request Remarks for ${vendor}`,
                        fieldtype: "Data",
                        reqd: 1
                    }
                ],
                resolve,
                "Send Revised Quotation Request",
                "Send"
            );
        });

        const res = await frappe.call({
            method: "alms_app.crms.doctype.car_quotation.car_quotation.create_revised_quotation",
            args: { old_id: id }
        });

        const new_id = res.message;

        await frappe.call({
            method: "alms_app.api.emailsService.email_sender",
            args: {
                name: purchaseForm,
                email_send_to: "FinanceHead To Quotation Company",
                payload: {
                    quotation_id: new_id,
                    email_phase: "Revised",
                    email_send_to: [vendor]
                }
            }
        });

        frappe.msgprint(`Revised request sent to ${vendor}`);
    });
}


/* ================================
 EXCEL EXPORT
================================ */
function exportToExcel(data) {

    let fields = [
        "location",
        "total_kms",
        "interest_rate",
        "ex_showroom_amount",
        "total_discount",
        "accessories",
        "ex_showroom_amount_net_of_discount",
        "registration_charges",
        "financed_amount",
        "total_emi"
    ];

    let rows = [];

    // Header
    let header = ["Field", ...data.map(q => q.finance_company)];
    rows.push(header);

    // Body
    fields.forEach(f => {
        let row = [f.replaceAll("_", " ").toUpperCase()];

        data.forEach(q => {
            row.push(q[f] ?? "-");
        });

        rows.push(row);
    });

    frappe.tools.downloadify({
        data: rows,
        file_name: "Quotation_Comparison.xlsx"
    });
}