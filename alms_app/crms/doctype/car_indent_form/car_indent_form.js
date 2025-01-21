


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

function updateStatus(frm) {
    frm.clear_custom_buttons();

    const buttons = [
        {
            label: "Reporting Head",
            field: "reporting_head_approval",
            current_status: frm.doc.reporting_head_approval,
        },
        {
            label: "HR",
            field: "hr_approval",
            current_status: frm.doc.hr_approval,
        },
        {
            label: "HR Head",
            field: "hr_head_approval",
            current_status: frm.doc.hr_head_approval,
        }
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

function setupFieldChangeHandlers(frm) {

    // frm.fields_dict["reporting_head_approval"].df.onchange = function () {
    //     const new_value = frm.doc.reporting_head_approval || "No Value";
    //     // alert(`Reporting Head Approval changed to: ${new_value} : ${frm.doc.name}`);
    //     if (frm.doc.reporting_head_approval =="Approved"){
    //         alert(frm.doc.reporting_head_approval)
    //         // send_email(frm.doc.name,"Reporting To HR")
    //         frm.save_or_update();
    //     }
    // };

    frm.fields_dict["hr_approval"].df.onchange = function () {
        if (frm.doc.hr_approval =="Approved"){
            send_email(frm.doc.name,"HR To HRHead")
            frm.save_or_update();
        }
    };

    frm.fields_dict["hr_head_approval"].df.onchange = function () {
        frm.set_value("status", "Approved");
        if (frm.doc.hr_head_approval =="Approved"){
            send_email(frm.doc.name,"HRHead To PurchaseTeam")
            frm.save_or_update();
        }
    };
}



function toggleFieldStatus(frm) {
    // alert('Hellow',frappe.session.designation)
    if (frappe.session.user === "reporting@gmail.com") {
        frm.set_df_property("reporting_head_approval", "read_only", 0);
    }
    if (frappe.session.user === "hr@gmail.com") {
        frm.set_df_property("hr_approval", "read_only", 0);
    } 
    if (frappe.session.user === "hrhead@gmail.com") {
        frm.set_df_property("hr_head_approval", "read_only", 0);
    } 

    if (frappe.session.user==="Administrator"){
        frm.set_df_property("reporting_head_approval", "read_only", 0);
        frm.set_df_property("hr_approval", "read_only", 0);
        frm.set_df_property("hr_head_approval", "read_only", 0);
    }
 
    // const status = frm.doc[field_name];
    // const is_read_only = status === "Approved" || status === "Rejected";
    // frm.set_df_property(field_name, "read_only", is_read_only);
    // frm.refresh_field(field_name);
}



frappe.ui.form.on("Car Indent Form", {
    onload: function (frm) {

        frm.set_df_property('employee_code', 'read_only', 1);
        frm.set_df_property('ex_showroom_price', 'read_only', 1);
        frm.set_df_property('discount', 'read_only', 1);
        frm.set_df_property('tcs', 'read_only', 1);
        frm.set_df_property('registration_charges', 'read_only', 1);
        frm.set_df_property('accessories', 'read_only', 1);
        frm.set_df_property('make', 'read_only', 1);
        frm.set_df_property('engine', 'read_only', 1);
        frm.set_df_property('colour', 'read_only', 1);
        frm.set_df_property('reporting_head_approval', 'read_only', 1);
        frm.set_df_property('hr_approval', 'read_only', 1);
        frm.set_df_property('hr_head_approval', 'read_only', 1);
        frm.set_df_property('status', 'read_only', 1);

        toggleFieldStatus(frm);
        setupFieldChangeHandlers(frm);
    },

    refresh: function (frm) {
        updateStatus(frm);
        toggleFieldStatus(frm);
    }
});