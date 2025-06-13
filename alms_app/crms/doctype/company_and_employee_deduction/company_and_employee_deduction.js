// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company and Employee Deduction", {
    onload(frm){
        // calculate_emi(frm);
        // calculate_employee_fields(frm)
    },
    refresh(frm) {
        // calculate_emi(frm);
        // calculate_employee_fields(frm)
    },

    // registration_charges: function(frm){
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // ex_showroom_amount_net_of_discount: function(frm){
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // interest_rate: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // tenure: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // financed_amount: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // residual_value: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // gst: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // insurance: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // fleet_management_repairs_and_tyres: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // assist: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // pickup_and_drop: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },

    // std_relief_car_non_accdt: function(frm) {
    //     calculate_emi(frm);
    //     // calculate_employee_fields(frm)
    // },
    finance_quotation_id: function(frm){
        calculate_emi(frm);
    }

    
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
    const interest_rate = (frm.doc.interest_rate || 0) / 100;  // Annual interest rate as a fraction
    const tenure = frm.doc.tenure || 0;  // Loan tenure in months
    const ex_showroom_amount_net_of_discount = frm.doc.ex_showroom_amount_net_of_discount || 0;
    const registration_charges = frm.doc.registration_charges || 0;
    const residual_value = frm.doc.residual_value || 0;
    const gst = frm.doc.gst || 0;

    const insurance = frm.doc.insurance || 0;
    const fleet_management_repairs_and_tyres = frm.doc.fleet_management_repairs_and_tyres || 0;
    const assist = frm.doc.assist || 0;
    const pickup_and_drop = frm.doc.pickup_and_drop || 0;
    const std_relief_car_non_accdt = frm.doc.std_relief_car_non_accdt || 0;


    // Financed amount = Ex-showroom + Registration Charges
    const financed_amount = ex_showroom_amount_net_of_discount + registration_charges;
    console.log('Financed Amount:', financed_amount); // Debugging line

    frm.set_value("financed_amount", Math.ceil(financed_amount));

    // Monthly interest rate (annual interest rate divided by 12)
    const monthly_rate = interest_rate / 12;
    console.log('Monthly Interest Rate:', Math.ceil(monthly_rate)); // Debugging line

    
    const pmt = PMT(monthly_rate, tenure, -financed_amount, residual_value, 1)
    console.log('pmt:', pmt); // Debugging line
    const gstPerMonth = gst / tenure;

    const emi_financing = pmt - gstPerMonth;

    frm.set_value("emi_financing", Math.ceil(emi_financing));

    // Additional fields
    const finance_emi_road_tax = emi_financing - (registration_charges / tenure);
    console.log('Finance EMI Road Tax:', finance_emi_road_tax); // Debugging line
    frm.set_value("finance_emi_road_tax", Math.ceil(finance_emi_road_tax));

    // const cess_percent = gst_and_cess_percent / 100;
    const gst_and_cess = finance_emi_road_tax * 45/100;
    console.log('GST and Cess:', gst_and_cess);
    frm.set_value("gst_and_cess", Math.ceil(gst_and_cess));

    const fms_rate = (18/100)
    const gst_on_fms = (insurance + fleet_management_repairs_and_tyres + assist + pickup_and_drop + std_relief_car_non_accdt) * fms_rate;
    console.log ('gst_on_fms',gst_on_fms);
    frm.set_value("gst_on_fms",Math.ceil(gst_on_fms));

    const total_emi = (emi_financing + gst_and_cess + insurance + fleet_management_repairs_and_tyres + assist + pickup_and_drop + std_relief_car_non_accdt + gst_on_fms);
    console.log("Total EMI", total_emi, emi_financing, gst_and_cess, insurance, fleet_management_repairs_and_tyres, assist, pickup_and_drop, std_relief_car_non_accdt, gst_on_fms);
    frm.set_value("total_emi", Math.ceil(total_emi));

    const quarterly_payment = total_emi * 3;
    console.log("quarterly_payment", quarterly_payment, total_emi);
    frm.set_value("quarterly_payment", Math.ceil(quarterly_payment));

    
    const interim_payment = quarterly_payment * 39/90;
    console.log("interim_payment", interim_payment);
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
    let employee_ex_showroom_amount_net_of_discount= frm.doc.employee_ex_showroom_amount_net_of_discount || 0;
    let employee_residual_value_percent= frm.doc.employee_residual_value_percent || 0;
    let employee_financed_amount=frm.doc.employee_financed_amount || 0;
    let employee_residual_value=frm.doc.employee_residual_value || 0;
    let employee_emi_financing=frm.doc.employee_emi_financing || 0;
    let employee_finance_emi_road_tax=frm.doc.employee_finance_emi_road_tax || 0;
    let employee_gst_and_cess=frm.doc.employee_gst_and_cess || 0;
    let employee_insurance=frm.doc.employee_insurance || 0;
    let employee_fleet_management=frm.doc.employee_fleet_management || 0;
    let employee_assist=frm.doc.employee_24x7_assist || 0;
    let employee_pickup_drop=frm.doc.employee_pickup_drop || 0;
    let employee_std_relief_car_non_accdt= frm.doc.employee_std_relief_car_non_accdt || 0;
    let employee_gst_on_fms= frm.doc.employee_gst_on_fms || 0;
    let employee_total_emi=frm.doc.employee_total_emi || 0;
    let employee_interim_payment=frm.doc.employee_interim_payment || 0;
    let employee_quarterly_payment= frm.doc.employee_quarterly_payment || 0;


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
                employee_ex_showroom_amount_net_of_discount= response.message.ex_showroom_amount_net_of_discount - frm.doc.ex_showroom_amount_net_of_discount;
                frm.set_value("employee_ex_showroom_amount_net_of_discount",Math.ceil(employee_ex_showroom_amount_net_of_discount));

                // employee registration charges field was deleted
                //initialising as 0 for now
                const employee_registration_charges=0;
                employee_financed_amount=employee_ex_showroom_amount_net_of_discount+ employee_registration_charges;
                frm.set_value("employee_financed_amount",Math.ceil(employee_financed_amount));

                // residual value given as = base price less discounts * residual_value percent
                const interest_rate = (frm.doc.interest_rate || 0) / 100;  // Annual interest rate as a fraction
                const tenure = frm.doc.tenure || 0; 
                const monthly_rate = interest_rate / 12;
                const gst = frm.doc.gst || 0;

                const pmt= PMT(monthly_rate, tenure,-employee_financed_amount,employee_residual_value,1);
                const gstPerMonth = gst / tenure;
                employee_emi_financing = pmt - gstPerMonth;
                frm.set_value("employee_emi_financing",Math.ceil(employee_emi_financing));

                employee_finance_emi_road_tax=employee_emi_financing-(employee_registration_charges/tenure);
                frm.set_value("employee_finance_emi_road_tax",Math.ceil(employee_finance_emi_road_tax));

                employee_gst_and_cess=employee_finance_emi_road_tax*45/100;
                frm.set_value("employee_gst_and_cess",Math.ceil(employee_gst_and_cess));

                employee_total_emi=employee_emi_financing+employee_gst_and_cess+employee_insurance+employee_fleet_management+employee_assist+employee_pickup_drop+employee_std_relief_car_non_accdt+employee_gst_on_fms;
                frm.set_value("employee_total_emi",Math.ceil(employee_total_emi));

                employee_quarterly_payment=employee_total_emi*3;
                frm.set_value("employee_quarterly_payment",Math.ceil(employee_quarterly_payment));
                
                employee_interim_payment=employee_quarterly_payment*39/90;
                frm.set_value("employee_interim_payment",Math.ceil(employee_interim_payment));

            }
            else{
                console.log("ELEEEEE");
            }
        },
        error: function (err) {
        console.error("Error fetching list data:", err);
        },
    });

}
