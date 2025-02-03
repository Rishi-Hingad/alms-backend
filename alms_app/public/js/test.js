frappe.listview_settings['Purchase Team Form'] = {
    onload: function (listview) {
        listview.page.add_inner_button('Custom Button', function () {
            let selected_docs = listview.get_checked_items();
            
            if (selected_docs.length === 0) {
                frappe.msgprint(__('Please select at least one record.'));
                return;
            }

            alert("Ok Done")
        }, "Actions"); // "Actions" section me button dikhayega
    }
};
