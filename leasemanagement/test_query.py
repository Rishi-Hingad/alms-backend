import frappe
def execute():
    try:
        # try fetching with capital C
        res = frappe.get_all("Lease Management", filters={"Company": "Dummy"}, limit=1)
        print("Success:", res)
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e))
execute()
