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

        # Only generate if table is empty
        if self.installment_date:
            return

        current_start = start_date
        installment_count = 0

        while current_start <= end_date:

            current_end = add_days(add_months(current_start, 3), -1)

            if current_end > end_date:
                current_end = end_date

            due_date = getdate(current_start).replace(day=15)

            self.append("installment_date", {
                "installment_no": installment_count + 1,
                "installment_start_date": current_start,
                "installment_end_date": current_end,
                "due_date": due_date
            })

            installment_count += 1
            current_start = add_months(current_start, 3)

        self.no_of_installments = installment_count


    def after_insert(self):
        update_vehicle_details(self)

    def on_update(self):
        update_vehicle_details(self)


def update_vehicle_details(doc):

    if not doc.employee_car_process_form:
        return

    car_process = frappe.get_doc(
        "Car Process",
        doc.employee_car_process_form
    )

    contract_document = car_process.contract_document

    vehicle_name = frappe.get_value(
        "Vehicle Details",
        {"employee_code_and_name": doc.employee_car_process_form},
        "name"
    )

    if not vehicle_name:
        return

    vehicle_doc = frappe.get_doc("Vehicle Details", vehicle_name)

    vehicle_doc.contract_number = doc.name
    vehicle_doc.contract_document = contract_document

    vehicle_doc.set("installment_payment", [])

    for row in doc.installment_date:

        vehicle_doc.append("installment_payment", {
            "installment_no": row.installment_no,
            "installment_start_date": row.installment_start_date,
            "installment_end_date": row.installment_end_date,
            "installment_amount": row.installment_amount if hasattr(row, "installment_amount") else 0,
            "installment_status": "Not Paid"
        })

    vehicle_doc.save(ignore_permissions=True, ignore_version=True)