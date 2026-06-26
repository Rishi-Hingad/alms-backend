frappe.provide('alms_app');

alms_app.restricted_modules = ['ALMS', 'CRMS', 'master'];

alms_app.restrict_listview = function (listview) {
    const doctype = listview.doctype;

    frappe.call({
        method: 'alms_app.utils.utils.get_doctype_module',
        args: { doctype: doctype },
        async: false,
        callback: function (r) {
            if (r.message && alms_app.restricted_modules.includes(r.message)) {
                frappe.call({
                    method: 'alms_app.utils.utils.can_view_alms_doctypes',
                    async: false,
                    callback: function (role_check) {
                        if (!role_check.message) {
                            $('.layout-main-section').hide();
                            $('.page-head').hide();
                            $('.page-title').hide();

                            frappe.msgprint({
                                title: __('Access Denied'),
                                indicator: 'red',
                                message: __('You do not have the required role "ALMS User" to access this module.')
                            });

                            setTimeout(function () {
                                window.location.href = '/app';
                            }, 1000);
                        }
                    }
                });
            }
        }
    });
};

frappe.listview_settings = new Proxy(frappe.listview_settings || {}, {
    get: function (target, doctype) {
        if (!target[doctype]) {
            target[doctype] = {};
        }

        const original_onload = target[doctype].onload;
        target[doctype].onload = function (listview) {
            alms_app.restrict_listview(listview);

            if (original_onload) {
                original_onload.call(this, listview);
            }
        };

        return target[doctype];
    }
});

$(document).on('form-load', function (e, frm) {
    const doctype = frm.doctype;

    frappe.call({
        method: 'alms_app.utils.utils.get_doctype_module',
        args: { doctype: doctype },
        async: false,
        callback: function (r) {
            if (r.message && ['ALMS', 'CRMS', 'master'].includes(r.message)) {
                frappe.call({
                    method: 'alms_app.utils.utils.can_view_alms_doctypes',
                    async: false,
                    callback: function (role_check) {
                        if (!role_check.message) {
                            frappe.msgprint({
                                title: __('Access Denied'),
                                indicator: 'red',
                                message: __('You do not have the required role "ALMS User" to access this form.')
                            });

                            setTimeout(function () {
                                window.location.href = '/app/home';
                            }, 1500);
                        }
                    }
                });
            }
        }
    });
});