import frappe
from frappe.model.document import Document
from frappe.utils import add_months, add_days, getdate


class ContractMaster(Document):

    def validate(self):
        self.generate_installments()

    def generate_installments(self):

        if not self.contract_start_date or not self.contract_end_date:
            return

        start_date = getdate(self.contract_start_date)
        end_date = getdate(self.contract_end_date)

        if start_date > end_date:
            frappe.throw("Contract End Date cannot be before Start Date")

        # Clear child table
        self.set("installment_date", [])

        current_start = start_date
        installment_count = 0

        while current_start <= end_date:
            current_end = add_days(add_months(current_start, 3), -1)

            if current_end > end_date:
                current_end = end_date

            self.append("installment_date", {
                "installment_start_date": current_start,
                "installment_end_date": current_end
            })

            installment_count += 1
            current_start = add_months(current_start, 3)

        self.no_of_installments = installment_count