// Copyright (c) 2024, Harsh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company and Employee Deduction", {
    refresh(frm) {
        calculate_emi(frm);
    },

    registration_charges: function(frm){
        calculate_emi(frm);
    },

    ex_showroom_amount_net_of_discount: function(frm){
        calculate_emi(frm);
    },

    interest_rate: function(frm) {
        calculate_emi(frm);
    },

    tenure: function(frm) {
        calculate_emi(frm);
    },

    financed_amount: function(frm) {
        calculate_emi(frm);
    },

    residual_value: function(frm) {
        calculate_emi(frm);
    },

    gst: function(frm) {
        calculate_emi(frm);
    },

    insurance: function(frm) {
        calculate_emi(frm);
    },

    fleet_management_repairs_and_tyres: function(frm) {
        calculate_emi(frm);
    },

    assist: function(frm) {
        calculate_emi(frm);
    },

    pickup_and_drop: function(frm) {
        calculate_emi(frm);
    },

    std_relief_car_non_accdt: function(frm) {
        calculate_emi(frm);
    },
    
    gst_and_cess_percent: function(frm) {
        calculate_emi(frm);
    }
});
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
    const gst_and_cess_percent = frm.doc.gst_and_cess_percent || 0;


    // Financed amount = Ex-showroom + Registration Charges
    const financed_amount = ex_showroom_amount_net_of_discount + registration_charges;
    console.log('Financed Amount:', financed_amount); // Debugging line

    frm.set_value("financed_amount", financed_amount);

    // Monthly interest rate (annual interest rate divided by 12)
    const monthly_rate = interest_rate / 12;
    console.log('Monthly Interest Rate:', monthly_rate); // Debugging line

    // PMT formula: -Loan amount * Monthly Rate * (1 + Monthly Rate)^Tenure / ((1 + Monthly Rate)^Tenure - 1)
    let emi = - (financed_amount * monthly_rate * Math.pow(1 + monthly_rate, tenure)) / (Math.pow(1 + monthly_rate, tenure) - 1);
    console.log('Pre-GST EMI:', emi); // Debugging line

    // Adjust for annuity due by multiplying by (1 + monthly_rate)
    emi = emi * (1 + monthly_rate); // Apply the "1" from the Excel formula
    console.log('Adjusted EMI (Annuity Due):', emi); // Debugging line

    // Correct EMI adjustment (make it positive)
    emi = Math.abs(emi); // Make EMI positive to match expected value
    console.log('Positive EMI (adjusted for sign):', emi); // Debugging line

    // Subtract residual value from EMI (to handle residual value as per the loan terms)
    const emi_with_residual_adjustment = emi - (residual_value / tenure);
    console.log('Final EMI (after residual value adjustment):', emi_with_residual_adjustment); // Debugging line

    // Subtract GST adjustment based on formula (C9 / C7)
    const emi_with_gst_adjustment = emi_with_residual_adjustment - (gst / tenure);
    console.log('Final EMI (after GST adjustment):', emi_with_gst_adjustment); // Debugging line

    // Round final EMI to 2 decimal places
    const final_emi = Math.round(emi_with_gst_adjustment * 100) / 100;
    console.log('Final EMI (Rounded):', final_emi); // Debugging line

    frm.set_value("emi_financing", final_emi);

    // Additional fields
    const finance_emi_road_tax = final_emi - (registration_charges / tenure);
    console.log('Finance EMI Road Tax:', finance_emi_road_tax); // Debugging line
    frm.set_value("finance_emi_road_tax", finance_emi_road_tax);

    const cess_percent = gst_and_cess_percent / 100;
    const gst_and_cess = finance_emi_road_tax * cess_percent;
    console.log('GST and Cess:', gst_and_cess, cess_percent);
    frm.set_value("gst_and_cess", gst_and_cess);

    const fms_rate = (18/100)
    const gst_on_fms = (insurance + fleet_management_repairs_and_tyres + assist + pickup_and_drop + std_relief_car_non_accdt) * fms_rate;
    console.log ('gst_on_fms',gst_on_fms);
    frm.set_value("gst_on_fms",gst_on_fms);

    const total_emi = (final_emi + gst_and_cess + insurance + fleet_management_repairs_and_tyres + assist + pickup_and_drop + std_relief_car_non_accdt + gst_on_fms);
    console.log("Total EMI", total_emi, final_emi, gst_and_cess, insurance, fleet_management_repairs_and_tyres, assist, pickup_and_drop, std_relief_car_non_accdt, gst_on_fms);
    frm.set_value("total_emi", total_emi);

    const quarterly_payment = total_emi * 3;
    console.log("quarterly_payment", quarterly_payment, total_emi);
    frm.set_value("quarterly_payment", quarterly_payment);
    

    // Refresh fields
    frm.refresh_field("financed_amount");
    frm.refresh_field("emi_financing");
    frm.refresh_field("finance_emi_road_tax");
    frm.refresh_field("gst_and_cess");
    frm.refresh_field("gst_on_fms");
    frm.refresh_field("total_emi");
    frm.refresh_field("quarterly_payment");
}
