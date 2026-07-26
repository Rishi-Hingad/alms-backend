import frappe
import os

def execute():
    bench_path = frappe.utils.get_bench_path()
    apps_txt_path = os.path.join(bench_path, "sites", "apps.txt")
    
    try:
        with open(apps_txt_path, "r") as f:
            apps = [line.strip() for line in f.read().splitlines() if line.strip()]
    except Exception:
        return
        
    if "alms_app" not in apps:
        print("Adding alms_app to apps.txt dynamically...")
        # Insert alms_app before lease_app so lease_app modules override alms_app modules
        if "lease_app" in apps:
            idx = apps.index("lease_app")
            apps.insert(idx, "alms_app")
        else:
            apps.append("alms_app")
            
        with open(apps_txt_path, "w") as f:
            f.write("\n".join(apps) + "\n")
        
        # Clear cache so frappe recognizes the new app immediately in this migrate run
        frappe.cache().delete_value("all_apps")
        frappe.cache().delete_value("app_modules")
        frappe.setup_module_map()
        
    # Also ensure it's in tabInstalled Applications
    installed_apps = frappe.get_installed_apps()
    if "alms_app" not in installed_apps:
        from frappe.installer import add_to_installed_apps
        print("Adding alms_app to tabInstalled Applications dynamically...")
        add_to_installed_apps("alms_app", rebuild_website=False)
        frappe.db.commit()

