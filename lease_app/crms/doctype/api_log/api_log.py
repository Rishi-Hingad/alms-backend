from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import nowdate

class APILog(Document):

    def autoname(self):
        if self.invoice_batch_doc:
            # LOG-<invoice_batch>-####
            self.name = make_autoname(f"LOG-{self.invoice_batch_doc}-.####")
        else:
            # LOG-YYYYMMDD-####
            date_str = nowdate().replace("-", "")
            self.name = make_autoname(f"LOG-{date_str}-.####")