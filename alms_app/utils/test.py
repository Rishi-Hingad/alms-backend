import frappe
def execute():
    try:
        scripts = frappe.get_all('Client Script', fields=['name', 'dt', 'script'])
        for s in scripts:
            if s.script and 'revised' in s.script.lower():
                print(f"--- Script: {s.name} (Doctype: {s.dt}) ---")
                print(s.script)
    except Exception as e:
        print("Error:", e)
