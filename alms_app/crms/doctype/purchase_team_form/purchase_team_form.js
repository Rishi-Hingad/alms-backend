function updateStatus(frm) {
    frm.clear_custom_buttons();

    const buttons = [
        {
            label: "Purchase Team",
            field: "status",
            current_status: frm.doc.purchase_team_status
        },
        {
            label: "Purchase Head",
            field: "status",
            current_status: frm.doc.purchase_head_status
        },
    ];

    buttons.forEach(button => {
        const status = button.current_status || "Pending";
        let status_color;

        switch (status) {
            case "Approved":
                status_color = "darkgreen";
                break;
            case "Rejected":
                status_color = "darkred";
                break;
            default:
                status_color = "gray";
        }

        frm.add_custom_button(`${button.label}: ${status}`, null).css({
            "background-color": status_color,
            "color": "white",
            "border-color": status_color,
            "cursor": "not-allowed"
        });
    });
}

function send_email(user,email_send_to){
    frappe.call({
        method: "alms_app.api.emailsService.email_sender",
        args: {
            name: user,
            email_send_to: email_send_to,
        },
        callback: function (response) {
            if (!response.exc) {
                // frappe.msgprint("Email sent successfully!");
            } else {
                frappe.msgprint({
                    title: "Error",
                    indicator: "red",
                    message: response.exc || "An unknown error occurred while sending the email.",
                });
            }
        },
        error: function (error) {
            frappe.msgprint({
                title: "Error",
                indicator: "red",
                message: error.message || "An unknown error occurred while sending the email.",
            });
        },
    });
}


function toggleFieldStatus(frm) {
    // if (frappe.session.designation === "Purchase Head") {
    if (frappe.session.user === "purchasehead@gmail.com") {
        frm.set_df_property("status", "read_only", true);
        frm.set_df_property("purchase_head_status", "read_only", false);
        frm.set_df_property("purchase_team_status", "read_only", true);
        frm.set_df_property("kilometers_per_year", "read_only", true);
        frm.set_df_property("tenure_in_years", "read_only", true);
        frm.set_df_property("total_kilometers", "read_only", true);
        frm.set_df_property("revised_ex_show_room_price", "read_only", true);
        frm.set_df_property("revised_discount", "read_only", true);
        frm.set_df_property("revised_tcs", "read_only", true);
        frm.set_df_property("revised_net_ex_showroom_price", "read_only", true);
        frm.set_df_property("revised_registration_charges", "read_only", true);
        frm.set_df_property("revised_accessories", "read_only", true);
        frm.set_df_property("revised_financed_amount", "read_only", true);
    }
    else if (frappe.session.user === "purchase@gmail.com") {
        frm.set_df_property("purchase_head_status", "read_only", true);
        frm.set_df_property("status", "read_only", true);
    }
    else{
        frm.set_df_property("status", "read_only", true);
        frm.set_df_property("purchase_team_status", "read_only", true);
        frm.set_df_property("kilometers_per_year", "read_only", true);
        frm.set_df_property("tenure_in_years", "read_only", true);
        frm.set_df_property("total_kilometers", "read_only", true);
        frm.set_df_property("revised_ex_show_room_price", "read_only", true);
        frm.set_df_property("revised_discount", "read_only", true);
        frm.set_df_property("revised_tcs", "read_only", true);
        frm.set_df_property("revised_net_ex_showroom_price", "read_only", true);
        frm.set_df_property("revised_registration_charges", "read_only", true);
        frm.set_df_property("revised_accessories", "read_only", true);
        frm.set_df_property("revised_financed_amount", "read_only", true);
        frm.set_df_property("purchase_head_status", "read_only", true);
        frm.set_df_property("status", "read_only", true);
    }

}

frappe.ui.form.on("Purchase Team Form", {
        refresh(frm) {

            updateStatus(frm);
            calculate_totals(frm);
            addButtonForAppovel(frm);
            toggleFieldStatus(frm);
        },
        onload(frm){
            updateStatus(frm);
            toggleFieldStatus(frm);
            addButtonForAppovel(frm); 
        },

        purchase_head_status: function(frm) {
            if (frm.doc.purchase_head_status === "Approved"){
                // const new_value = frm.doc.purchase_head_status || "No Value";
                frm.set_value("status", frm.doc.purchase_head_status); // Correctly set the "status" field
                // alert(`Purchase Head Approval changed to: ${new_value} : ${frm.doc.name}`);
                send_email(frm.doc.name,"PurchaseHead To FinanceTeam")
                frm.save_or_update();
            }
        },
    

        purchase_team_status: function(frm) {
            alert(frm.doc.purchase_head_status)
            if (frm.doc.purchase_team_status === "Approved"){
            // const new_value = frm.doc.purchase_team_status || "No Value";
            // alert(`Purchase Team Approval changed to: ${new_value} : ${frm.doc.name}`);
            send_email(frm.doc.name,"PurchaseTeam To PurchaseHead")
            frm.save_or_update();
            }
        },


        revised_ex_show_room_price: function(frm) {
            calculate_totals(frm);
        },
    
        revised_discount: function(frm) {
            calculate_totals(frm);
        },
    
        revised_tcs: function(frm) {
            calculate_totals(frm);
        },
    
        revised_registration_charges: function(frm) {
            calculate_totals(frm);
        },
    
        revised_accessories: function(frm) {
            calculate_totals(frm);
        },

        kilometers_per_year: function(frm) {
            calculate_totals(frm);
        },

        tenure_in_years: function(frm) {
            calculate_totals(frm);
        },


});





function calculate_totals(frm) {
    const revised_ex_show_room_price = frm.doc.revised_ex_show_room_price || 0;
    const revised_tcs = frm.doc.revised_tcs || 0;
    const revised_accessories = frm.doc.revised_accessories || 0;
    const revised_discount = frm.doc.revised_discount || 0;
    const revised_registration_charges = frm.doc.revised_registration_charges || 0;
    const kilometers_per_year = frm.doc.kilometers_per_year || 0;
    const tenure_in_years = frm.doc.tenure_in_years || 0;

    frm.set_value("total_kilometers", kilometers_per_year * tenure_in_years);

    const revised_net_ex_showroom_price = revised_ex_show_room_price + revised_tcs - revised_discount;
    frm.set_value("revised_net_ex_showroom_price", revised_net_ex_showroom_price);

    const finance_amount = (revised_ex_show_room_price + revised_tcs - revised_discount) + revised_accessories + revised_registration_charges;
    frm.set_value("revised_financed_amount", finance_amount);
}

