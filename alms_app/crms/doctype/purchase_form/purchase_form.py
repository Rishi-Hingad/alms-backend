# Copyright (c) 2026, Rishi Hingad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class PurchaseForm(Document):
    def validate(self):
        # Calculate revised fields if applicable
        ex_show_room = flt(self.revised_ex_show_room_price)
        discount = flt(self.revised_discount)
        tcs = flt(self.revised_tcs)
        reg_charges = flt(self.revised_registration_charges)
        accessories = flt(self.revised_accessories)

        if ex_show_room or discount or tcs or reg_charges or accessories:
            self.revised_net_ex_showroom_price = ex_show_room - discount + tcs
            self.revised_financed_amount = self.revised_net_ex_showroom_price + reg_charges + accessories

        km_per_year = flt(self.kilometers_per_year)
        tenure = flt(self.tenure_in_years)
        
        if km_per_year and tenure:
            self.total_kilometers = km_per_year * tenure
        else:
            self.total_kilometers = ""

    def before_save(self):
        # Clear any dummy.pdf defaults from Custom Field or Property Setter that might have been applied to this document
        for field in self.meta.get("fields", {"fieldtype": "Attach"}):
            if self.get(field.fieldname) and "/files/dummy.pdf" in self.get(field.fieldname):
                self.set(field.fieldname, None)

@frappe.whitelist()
def force_delete(docname):
    # Check permissions manually since it's whitelisted
    if frappe.session.user != "Administrator":
        frappe.throw("Only Administrator can Force Delete")
    
    doc = frappe.get_doc("Purchase Form", docname)
    
    # Delete Approval Entries linked to this Purchase Form
    entries = frappe.get_all("Approval Entry", filters={"applied_to_doctype": "Purchase Form", "record": docname})
    for entry in entries:
        frappe.delete_doc("Approval Entry", entry.name, force=1)
        
    # Delete Selected Vendor linked to this Purchase Form
    if doc.all_quotations_ref_no:
        try:
            frappe.delete_doc("Selected Vendor", doc.all_quotations_ref_no, force=1)
        except Exception:
            pass
        
    # Delete the Purchase Form
    frappe.delete_doc("Purchase Form", docname, force=1)
    
    frappe.msgprint("Deleted successfully")
