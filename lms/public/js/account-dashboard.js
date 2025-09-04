$(document).ready(function() {
    
    function checkAndExecute() {
        var route = window.location.hash;
        var frappRoute = frappe.get_route_str ? frappe.get_route_str() : 'frappe.get_route_str not available';
        var frappRouteArray = frappe.get_route ? frappe.get_route() : 'frappe.get_route not available';
        
        // console.log("=== Route Debug Info ===");
        // console.log("window.location.hash:", route);
        // console.log("frappe.get_route_str():", frappRoute);
        // console.log("frappe.get_route():", frappRouteArray);
        // console.log("window.location.href:", window.location.href);
        // console.log("window.location.pathname:", window.location.pathname);
        // console.log("=======================");
        
        // Try multiple route detection methods
        var isAccountDashboard = false;
        
        if (route && (route.includes('account-dashboard') || route.includes('account_dashboard'))) {
            isAccountDashboard = true;
            console.log("Detected via window.location.hash");
        }
        
        if (frappRoute && (frappRoute.includes('account-dashboard') || frappRoute.includes('account_dashboard'))) {
            isAccountDashboard = true;
            console.log("Detected via frappe.get_route_str");
        }
        
        if (window.location.href.includes('account-dashboard') || window.location.href.includes('account_dashboard')) {
            isAccountDashboard = true;
            console.log("Detected via window.location.href");
        }
        
        if (isAccountDashboard) {
            console.log("Account dashboard detected, executing bulk update");
            executeBulkUpdate();
        } else {
            console.log("Not on account dashboard page");
        }
    }
    
    function executeBulkUpdate() {
        // console.log("Starting bulk update execution");
        frappe.call({
            method: "lms.lease_management_system.doctype.lease_management.lease_management.bulk_update_agreement_status",
            callback: function(r) {
                console.log("Response:", r);
                // if (r.message && r.message.updated) {
                //     frappe.show_alert({
                //         message: 'Lease Statuses Updated',
                //         indicator: 'green'
                //     });
                // }
            },
            error: function(r) {
                console.error("Error:", r);
            }
        });
    }
    
    // Check immediately
    setTimeout(checkAndExecute, 1000);
    setTimeout(checkAndExecute, 3000);
    setTimeout(checkAndExecute, 5000);
    
    // Listen for hash changes
    $(window).on('hashchange', function() {
        console.log("Hash changed, checking route");
        setTimeout(checkAndExecute, 500);
    });
});
