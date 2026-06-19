import frappe

def restore():
    # Doctypes
    doctypes = [
        "Car Process Config",
        "Car Process Step",
        "Purchase Form"
    ]
    for dt in doctypes:
        try:
            doc = frappe.get_doc("DocType", dt)
            doc.save()
            print(f"Restored doctype: {dt}")
        except Exception as e:
            print(f"Failed to restore {dt}: {e}")

    # Number Cards
    cards = [
        "Pending Purchase Form",
        "Rejected Purchase Form",
        "Total Purchase Form"
    ]
    for card in cards:
        try:
            doc = frappe.get_doc("Number Card", card)
            doc.save()
            print(f"Restored number card: {card}")
        except Exception as e:
            print(f"Failed to restore {card}: {e}")
