frappe.listview_settings['Employee'] = {
    onload: function (listview) {
        listview.page.add_action_item(__("Send Credential Email"), function () {
            const selected_records = listview.get_checked_items();
            if (selected_records.length === 0) return;

            frappe.call({
                method: "alms_app.master.doctype.employee.employee.send_credential_email",
                args: {
                    employee_names: selected_records.map(r => r.name)
                },
                callback: function (r) {
                    if (r.message) {
                        // Backend will handle showing msgprints directly if needed, but we can also handle returned values here if required.
                    }
                }
            });
        });
    },
};