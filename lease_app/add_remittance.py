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
        
    apps_dir = os.path.join(bench_path, "apps")

    if "remittance_tool" not in apps:
        print("Adding remittance_tool to apps.txt dynamically...")
        # Insert remittance_tool before lease_app so lease_app modules override remittance_tool modules
        if "lease_app" in apps:
            idx = apps.index("lease_app")
            apps.insert(idx, "remittance_tool")
        else:
            apps.append("remittance_tool")
            
        with open(apps_txt_path, "w") as f:
            f.write("\n".join(apps) + "\n")
        
        # Ensure the environment can import remittance_tool before setting up the module map
        import sys
        if apps_dir not in sys.path:
            sys.path.insert(0, apps_dir)
        lease_app_dir = os.path.join(apps_dir, 'lease_app')
        remittance_dir = os.path.join(lease_app_dir, 'remittance')
        if lease_app_dir not in sys.path:
            sys.path.insert(0, lease_app_dir)
        if remittance_dir not in sys.path:
            sys.path.insert(0, remittance_dir)

        # Clear cache so frappe recognizes the new app immediately in this migrate run
        frappe.cache().delete_value("all_apps")
        frappe.cache().delete_value("app_modules")
        frappe.setup_module_map()
        
    # Also ensure it's in tabInstalled Applications
    installed_apps = frappe.get_installed_apps()
    if "remittance_tool" not in installed_apps:
        from frappe.installer import add_to_installed_apps
        print("Adding remittance_tool to tabInstalled Applications dynamically...")
        add_to_installed_apps("remittance_tool", rebuild_website=False)
        frappe.db.commit()

