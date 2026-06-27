frappe.listview_settings['Car Indent Form'] = {
    onload: function(listview) {
        frappe.call({
            method: 'lease_app.crms.doctype.car_indent_form.car_indent_form.can_view_car_indent_list',
            async: false,
            callback: function(r) {
                if (!r.message) {
                    $('.layout-main-section').hide();
                    $('.page-head').hide();
                    $('.page-title').hide();
                    
                    frappe.msgprint({
                        title: __('Access Denied'),
                        indicator: 'red',
                        message: __('You do not have the required role "ALMS User" to view this list.')
                    });
                    
                    setTimeout(function() {
                        window.location.href = '/app';
                    }, 1000);
                }
            }
        });
    },
    
    refresh: function(listview) {
        frappe.call({
            method: 'lease_app.crms.doctype.car_indent_form.car_indent_form.can_view_car_indent_list',
            callback: function(r) {
                if (!r.message) {
                    $('.layout-main-section').hide();
                    $('.page-head').hide();
                    $('.page-title').hide();
                    
                    frappe.msgprint({
                        title: __('Access Denied'),
                        indicator: 'red',
                        message: __('You do not have the required role "ALMS User" to view this list.')
                    });
                    
                    setTimeout(function() {
                        window.location.href = '/app';
                    }, 1000);
                }
            }
        });
    }
};