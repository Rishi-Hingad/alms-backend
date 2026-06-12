// Removed manual send_email logic (handled by Approval Router backend)


frappe.ui.form.on("Company and Employee Deduction", {
    onload(frm){
        if (window.setup_approval_ui) window.setup_approval_ui(frm);
    },
    refresh(frm) {
        if (window.setup_approval_ui) window.setup_approval_ui(frm);
    },
    finance_quotation_id: function(frm){
        calculate_emi(frm);
    },
    assist: function(frm){
        calculate_emi(frm);
    },
    accessory: function(frm){
        calculate_emi(frm);
    },
    discount_excluding_gst: function(frm){
        calculate_emi(frm);
    },
    base_price_less_discounts: function(frm){
        calculate_emi(frm);
    },
    total_discount: function(frm){
        calculate_emi(frm);
    },
    pickup_and_drop: function(frm){
        calculate_emi(frm);
    },
    std_relief_car_non_accdt: function(frm){
        calculate_emi(frm);
    },
    employee_insurance: function(frm){
        calculate_emi(frm);
    },
    employee_fleet_management: function(frm){
        calculate_emi(frm);
    },
    employee_24x7_assist: function(frm){
        calculate_emi(frm);
    },
    employee_pickup_drop: function(frm){
        calculate_emi(frm);
    },
    employee_std_relief_car_non_accdt: function(frm){
        calculate_emi(frm);
    },

    // Legacy status handlers removed - handled by Approval Matrix now


    
});


function PMT(rate, nper, pv, fv = 0, type = 0) {
 if (rate === 0) return -(pv + fv) / nper;
 const pow = Math.pow(1 + rate, nper);
 let pmt = -(
 (pv * pow + fv) * rate / (pow - 1)
 );
 if (type === 1) pmt /= (1 + rate);
 return pmt;
}


function calculate_emi(frm) {
    const interest_rate = (parseFloat(frm.doc.interest_rate) || 0) / 100;  // Annual interest rate as a fraction
    const tenure = parseFloat(frm.doc.tenure) || 0;  // Loan tenure in months
    const ex_showroom_amount_net_of_discount = parseFloat(frm.doc.ex_showroom_amount_net_of_discount) || 0;
    const registration_charges = parseFloat(frm.doc.registration_charges) || 0;
    const residual_value = parseFloat(frm.doc.residual_value) || 0;
    const gst = parseFloat(frm.doc.gst) || 0;

    const insurance = parseFloat(frm.doc.insurance) || 0;
    
    const fleet_management_repairs_and_tyres = parseFloat(frm.doc.fleet_management_repairs_and_tyres) || 0;
    const assist = parseFloat(frm.doc.assist) || 0;
    const pickup_and_drop = parseFloat(frm.doc.pickup_and_drop) || 0;
    const std_relief_car_non_accdt = parseFloat(frm.doc.std_relief_car_non_accdt) || 0;
    // console.log("insurance: ", insurance, fleet_management_repairs_and_tyres, assist,pickup_and_drop, std_relief_car_non_accdt);


    // Financed amount = Ex-showroom + Registration Charges
    const financed_amount = ex_showroom_amount_net_of_discount + registration_charges;
    // console.log('Financed Amount:', financed_amount); // Debugging line

    frm.set_value("financed_amount", Math.ceil(financed_amount));

    // Monthly interest rate (annual interest rate divided by 12)
    const monthly_rate = interest_rate / 12;
    // console.log('Monthly Interest Rate:', monthly_rate); // Debugging line

    
    const pmt = PMT(monthly_rate, tenure, -financed_amount, residual_value, 1)
    // console.log('pmt:', pmt); // Debugging line
    const gstPerMonth = gst / tenure;
    // console.log("gstPerMonth",gstPerMonth)
    const emi_financing = pmt - gstPerMonth;
    // console.log("+++",emi_financing)
    frm.set_value("emi_financing", Math.ceil(emi_financing));

    // Additional fields
    const finance_emi_road_tax = emi_financing - (registration_charges / tenure);
    // console.log('Finance EMI Road Tax:', finance_emi_road_tax); // Debugging line
    frm.set_value("finance_emi_road_tax", Math.ceil(finance_emi_road_tax));

    // const cess_percent = gst_and_cess_percent / 100;
    const gst_and_cess = finance_emi_road_tax * 45/100;
    // console.log('GST and Cess:', gst_and_cess);
    frm.set_value("gst_and_cess", Math.ceil(gst_and_cess));

    const fms_rate = (18/100)
    const gst_on_fms = (insurance + fleet_management_repairs_and_tyres + assist + pickup_and_drop + std_relief_car_non_accdt) *fms_rate;
    // console.log ('gst_on_fms',gst_on_fms);
    frm.set_value("gst_on_fms",Math.ceil(gst_on_fms));

    const total_emi = (emi_financing + gst_and_cess + insurance + fleet_management_repairs_and_tyres + assist + pickup_and_drop + std_relief_car_non_accdt + gst_on_fms);
    // console.log("Total EMI", total_emi, emi_financing, gst_and_cess, insurance, fleet_management_repairs_and_tyres, assist, pickup_and_drop, std_relief_car_non_accdt, gst_on_fms);
    frm.set_value("total_emi", Math.ceil(total_emi));

    const quarterly_payment = total_emi * 3;
    // console.log("quarterly_payment", quarterly_payment, total_emi);
    frm.set_value("quarterly_payment", Math.ceil(quarterly_payment));

    
    const interim_payment = quarterly_payment * 39/90;
    // console.log("interim_payment", interim_payment);
    frm.set_value("interim_payment", Math.ceil(interim_payment));
    

    // Refresh fields
    frm.refresh_field("financed_amount");
    frm.refresh_field("emi_financing");
    frm.refresh_field("finance_emi_road_tax");
    frm.refresh_field("gst_and_cess");
    frm.refresh_field("gst_on_fms");
    frm.refresh_field("total_emi");
    frm.refresh_field("quarterly_payment");
    frm.refresh_field("interim_payment");
    calculate_employee_fields(frm);
}


function calculate_employee_fields(frm){
    let employee_ex_showroom_amount_net_of_discount= parseFloat(frm.doc.employee_ex_showroom_amount_net_of_discount) || 0;
    let employee_residual_value_percent= parseFloat(frm.doc.employee_residual_value_percent) || 0;
    let employee_financed_amount=parseFloat(frm.doc.employee_financed_amount) || 0;
    let employee_residual_value=parseFloat(frm.doc.employee_residual_value) || 0;
    let employee_emi_financing=parseFloat(frm.doc.employee_emi_financing) || 0;
    let employee_finance_emi_road_tax=parseFloat(frm.doc.employee_finance_emi_road_tax) || 0;
    let employee_gst_and_cess=parseFloat(frm.doc.employee_gst_and_cess) || 0;
    let employee_insurance=parseFloat(frm.doc.employee_insurance) || 0;
    let employee_fleet_management=parseFloat(frm.doc.employee_fleet_management) || 0;
    let employee_assist=parseFloat(frm.doc.employee_24x7_assist) || 0;
    let employee_pickup_drop=parseFloat(frm.doc.employee_pickup_drop) || 0;
    let employee_std_relief_car_non_accdt= parseFloat(frm.doc.employee_std_relief_car_non_accdt) || 0;
    let employee_gst_on_fms= parseFloat(frm.doc.employee_gst_on_fms) || 0;
    let employee_total_emi=parseFloat(frm.doc.employee_total_emi) || 0;
    let employee_interim_payment=parseFloat(frm.doc.employee_interim_payment) || 0;
    let employee_quarterly_payment= parseFloat(frm.doc.employee_quarterly_payment) || 0;


    frappe.call({
        method: "frappe.client.get",
        args: {
        doctype: "Car Quotation",
        name:frm.doc.finance_quotation_id,
        },
        callback: function (response) {
            if(response){
                console.log("found found");
                console.log(response);
                console.log(response.message.ex_showroom_amount_net_of_discount);
                console.log(frm.doc.ex_showroom_amount_net_of_discount);
                // employee_ex_showroom_amount_net_of_discount= response.message.ex_showroom_amount_net_of_discount - frm.doc.ex_showroom_amount_net_of_discount;
                employee_ex_showroom_amount_net_of_discount= Math.ceil(response.message.ex_showroom_amount_net_of_discount - frm.doc.ex_showroom_amount_net_of_discount);
                frm.set_value("employee_ex_showroom_amount_net_of_discount",Math.ceil(employee_ex_showroom_amount_net_of_discount));

                // employee registration charges field was deleted
                //initialising as 0 for now
                const employee_registration_charges=0;
                // employee_financed_amount=employee_ex_showroom_amount_net_of_discount+ employee_registration_charges;
                employee_financed_amount=Math.ceil(employee_ex_showroom_amount_net_of_discount+ employee_registration_charges);
                frm.set_value("employee_financed_amount",employee_financed_amount);

                // residual value given as = base price less discounts * residual_value percent
                const interest_rate = (parseFloat(frm.doc.interest_rate) || 0) / 100;  // Annual interest rate as a fraction
                const tenure = parseFloat(frm.doc.tenure) || 0; 
                const monthly_rate = interest_rate / 12;
                const gst = 0;  //field was deleted

                const pmt= PMT(monthly_rate, tenure,-employee_financed_amount,employee_residual_value,1);
                const gstPerMonth = gst / tenure;
                employee_emi_financing = Math.ceil(pmt - gstPerMonth);
                frm.set_value("employee_emi_financing",employee_emi_financing);

                employee_finance_emi_road_tax=Math.ceil(employee_emi_financing-(employee_registration_charges/tenure));
                frm.set_value("employee_finance_emi_road_tax",employee_finance_emi_road_tax);

                employee_gst_and_cess=Math.ceil(employee_finance_emi_road_tax*45/100);
                frm.set_value("employee_gst_and_cess",employee_gst_and_cess);

                employee_total_emi=Math.ceil(employee_emi_financing+employee_gst_and_cess+employee_insurance+employee_fleet_management+employee_assist+employee_pickup_drop+employee_std_relief_car_non_accdt+employee_gst_on_fms);
                frm.set_value("employee_total_emi",employee_total_emi);

                employee_quarterly_payment=Math.ceil(employee_total_emi*3);
                frm.set_value("employee_quarterly_payment",employee_quarterly_payment);
                
                employee_interim_payment=Math.ceil(employee_quarterly_payment*39/90);
                frm.set_value("employee_interim_payment",employee_interim_payment);


                console.log('Financed Amount:', employee_financed_amount); 
                console.log('ex showroom:', employee_ex_showroom_amount_net_of_discount);
                console.log('pmt:', pmt);
                console.log('gst:', gst); 
                console.log('emi financing:', employee_emi_financing);
                console.log('emi road tax:', employee_finance_emi_road_tax);// Debugging line // Debugging line// Debugging line
                console.log('gst n cess:', employee_gst_and_cess);
                console.log('total emi:', employee_total_emi);
                console.log("quarterly", employee_quarterly_payment);
                console.log('interim:', employee_interim_payment);
            }
            else{
                console.log("Doc not found");
            }
        },
        error: function (err) {
        console.error("Error fetching list data:", err);
        },
    });

}

// Removed legacy toggleFieldStatus and updateStatus logic
