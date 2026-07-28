import frappe
import os
import sys
import importlib

def execute():
    bench_path = frappe.utils.get_bench_path()
    apps_txt_path = os.path.join(bench_path, "sites", "apps.txt")
    apps_dir = os.path.join(bench_path, "apps")

    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    monorepo_dir = os.path.dirname(pkg_dir)
    alms_dir = os.path.join(monorepo_dir, "alms_app")
    approval_dir = os.path.join(monorepo_dir, "approval_app")
    remittance_dir = os.path.join(monorepo_dir, "remittance")

    for p in [alms_dir, approval_dir, remittance_dir, monorepo_dir, apps_dir]:
        if os.path.exists(p) and p not in sys.path:
            sys.path.insert(0, p)

    importlib.invalidate_caches()

    try:
        with open(apps_txt_path, "r") as f:
            apps = [line.strip() for line in f.read().splitlines() if line.strip()]
    except Exception:
        apps = []

    # Ensure all monorepo apps are listed in apps.txt
    needed_apps = ["lease_app", "alms_app", "remittance_tool", "approval_app"]
    updated_apps = False
    for app_name in needed_apps:
        if app_name not in apps:
            apps.append(app_name)
            updated_apps = True

    if updated_apps:
        with open(apps_txt_path, "w") as f:
            f.write("\n".join(apps) + "\n")
        frappe.cache().delete_value("all_apps")
        frappe.cache().delete_value("app_modules")
        try:
            frappe.setup_module_map()
        except Exception as e:
            print(f"Warning setting up module map: {e}")

    # Ensure all monorepo apps are in tabInstalled Applications
    try:
        installed_apps = frappe.get_installed_apps()
        from frappe.installer import add_to_installed_apps
        for app_name in needed_apps:
            if app_name not in installed_apps:
                print(f"Adding {app_name} to tabInstalled Applications dynamically...")
                add_to_installed_apps(app_name, rebuild_website=False)
        frappe.db.commit()
    except Exception as e:
        print(f"Warning adding apps to installed apps: {e}")

    # Align tabModule Def app_name associations so Frappe links every module to an installed app
    try:
        frappe.db.sql("UPDATE `tabModule Def` SET app_name = 'lease_app' WHERE module_name IN ('Lease Management System', 'Car and Lease', 'Lease Masters')")
        frappe.db.sql("UPDATE `tabModule Def` SET app_name = 'alms_app' WHERE module_name IN ('ALMS', 'master', 'CRMS')")
        frappe.db.sql("UPDATE `tabModule Def` SET app_name = 'approval_app' WHERE module_name = 'Approval'")
        frappe.db.sql("UPDATE `tabModule Def` SET app_name = 'remittance_tool' WHERE module_name = 'Remittance Tool'")
        frappe.db.commit()
    except Exception as e:
        print(f"Warning updating Module Def app_names: {e}")

    # Force reset custom flag, clear stale field_order Property Setters, and import Vendor Master directly from JSON
    try:
        if frappe.db.exists("DocType", "Vendor Master"):
            frappe.db.sql("UPDATE `tabDocType` SET custom = 0 WHERE name = 'Vendor Master'")
            frappe.db.sql("DELETE FROM `tabProperty Setter` WHERE doc_type = 'Vendor Master' AND property = 'field_order'")
            vm_path = os.path.join(monorepo_dir, "alms_app", "crms", "doctype", "vendor_master", "vendor_master.json")
            if os.path.exists(vm_path):
                from frappe.modules.import_file import import_file_by_path
                import_file_by_path(vm_path, force=True, ignore_version=True)
                print("Successfully reloaded Vendor Master directly from JSON path!")
            else:
                frappe.reload_doc("crms", "doctype", "vendor_master", force=True)
            frappe.clear_cache(doctype="Vendor Master")
            frappe.db.commit()
    except Exception as e:
        print(f"Warning reloading Vendor Master: {e}")
