import frappe
from openpyxl import load_workbook
from frappe.model.document import Document
import pandas as pd 
from frappe.utils.file_manager import save_file
import xlrd
from alms_app.api.emailsService import email_sender
from frappe.utils import flt
import math

class CarQuotation(Document):

    def on_update(self):
        if self.status == "Pending":
            handle_no_approved_case(self)

    def before_insert(self):
        # CASE 1: NEW quotation (root)
        if self.quotation_status == "New":
            self.root_quotation = self.name
            self.version_number = 1

        # CASE 2: REVISED quotation
        elif self.quotation_status == "Revised":

            if not self.revised_modify_quotation_id:
                frappe.throw("Missing base quotation")

            parent = frappe.get_doc("Car Quotation", self.revised_modify_quotation_id)

            # Root stays same
            self.root_quotation = parent.root_quotation or parent.name

            # Parent linkage
            self.parent_quotation = parent.name

            # Version increment
            self.version_number = (parent.version_number or 1) + 1

            # Naming logic
            self.name = f"{self.root_quotation}-v{self.version_number}"

    def validate(self):
        self.sync_status()
        self.calculate_quarterly_payment()
    
    def calculate_quarterly_payment(self):
        total_emi = flt(self.total_emi)

        if total_emi < 0:
            frappe.throw("Total EMI cannot be negative")

        self.quarterly_payment = total_emi * 4

    def sync_status(self):
        ft = (self.finance_team_status or "").strip().lower()
        fh = (self.finance_head_status or "").strip().lower()

        # Normalize
        if ft in ["", "-select-"]:
            self.finance_team_status = "Pending"
            ft = "pending"

        if fh in ["", "-select-"]:
            self.finance_head_status = "Pending"
            fh = "pending"

        # ===== STATUS LOGIC =====
        if ft == "rejected" or fh == "rejected":
            self.status = "Rejected"

        elif ft == "approved" and fh == "approved":
            self.status = "Approved"

            # enforce only one approved
            reject_other_quotations(self)

        else:
            self.status = "Pending"


    def after_insert(self):
        try:
            employee_details = self.employee_details
            finance_company = self.finance_company
            ref_no = self.name

            if not employee_details or not finance_company or not ref_no:
                frappe.log_error("Missing required values in CarQuotation", "CarQuotation Error")
            else:
                # Step 1: Check if Selected Vendor exists
                selected_vendor = frappe.db.get_value(
                    "Selected Vendor",
                    {"employee_details": employee_details},
                    "name"
                )

                if selected_vendor:
                    doc = frappe.get_doc("Selected Vendor", selected_vendor)

                    # Check duplicate
                    exists = any(
                        row.finance_company == finance_company and row.ref_no == ref_no
                        for row in doc.selected_finance_company
                    )

                    if not exists:
                        doc.append("selected_finance_company", {
                            "finance_company": finance_company,
                            "ref_no": ref_no
                        })
                        doc.save(ignore_permissions=True)

                else:
                    # Create new Selected Vendor
                    doc = frappe.get_doc({
                        "doctype": "Selected Vendor",
                        "employee_details": employee_details,
                        "selected_finance_company": [
                            {
                                "finance_company": finance_company,
                                "ref_no": ref_no
                            }
                        ]
                    })
                    doc.insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "CarQuotation after_insert Error")
        
        try:
            email_sender(
                name=self.employee_details,
                email_send_to="Finance Fill Quotation Acknowledgement",
                payload={
                    "vendors": [self.finance_company],
                    "email_phase": "Revised" if self.quotation_status == "Revised" else "Initial"
                }
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "ACK EMAIL FAILED")

        

def restore_other_quotations(doc):
    others = frappe.get_all(
        "Car Quotation",
        filters={
            "employee_details": doc.employee_details,
            "name": ["!=", doc.name]
        },
        pluck="name"
    )

    for q in others:
        q_doc = frappe.get_doc("Car Quotation", q)

        if q_doc.status != "Rejected":
            continue

        q_doc.finance_team_status = "Pending"
        q_doc.finance_head_status = "Pending"
        q_doc.status = "Pending"

        q_doc.save(ignore_permissions=True)

def handle_no_approved_case(doc):
    approved_exists = frappe.db.exists(
        "Car Quotation",
        {
            "employee_details": doc.employee_details,
            "status": "Approved"
        }
    )

    if not approved_exists:
        others = frappe.get_all(
            "Car Quotation",
            filters={
                "employee_details": doc.employee_details
            },
            pluck="name"
        )

        for q in others:
            q_doc = frappe.get_doc("Car Quotation", q)

            if q_doc.status == "Rejected":
                q_doc.finance_team_status = "Pending"
                q_doc.finance_head_status = "Pending"
                q_doc.status = "Pending"

                q_doc.save(ignore_permissions=True)


@frappe.whitelist()
def process_uploaded_file(file_url):
    if not file_url:
            frappe.throw("No file attached for upload.")

    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_path = file_doc.get_full_path()

        if file_path.endswith(".xlsx"):
            data_frame = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith(".xls"):
            data_frame = pd.read_excel(file_path, engine='xlrd')
        elif file_path.endswith(".csv"):
            data_frame = pd.read_csv(file_path)

        else:
            frappe.throw("Unsupported file format. Please upload an Excel or CSV file.")

        for index, row in data_frame.iterrows():
            car_quotation_item = frappe.get_doc({
                "doctype": "Car Quotation",
                "finance_company": row.get("finance_company"),
                "accessory": row.get("accessory"),
                "gst_and_cess": row.get("gst_and_cess"),
                "employee_details": row.get("employee_details"),
                "discount_excluding_gst": row.get("discount_excluding_gst"),
                "insurance": row.get("insurance"),
                "location": row.get("location"),
                "base_price_less_discounts": row.get("base_price_less_discounts"),
                "fleet_management_repairs_and_tyres": row.get("fleet_management_repairs_and_tyres"),
                "kms": row.get("kms"),
                "total_discount": row.get("total_discount"),
                "24x7_assist": row.get("24x7_assist"),
                "variant": row.get("variant"),
                "ex_showroom_amount_net_of_discount": row.get("ex_showroom_amount_net_of_discount"),
                "pickup_and_drop": row.get("pickup_and_drop"),
                "quote": row.get("quote"),
                "registration_charges": row.get("registration_charges"),
                "interest_rate": row.get("interest_rate"),
                "residual_value_percent": row.get("residual_value_percent"),
                "std_relief_car_non_accdt": row.get("std_relief_car_non_accdt"),
                "tenure": row.get("tenure"),
                "financed_amount": row.get("financed_amount"),
                "gst_on_fms": row.get("gst_on_fms"),
                "base_price_excluding_gst": row.get("base_price_excluding_gst"),
                "total_emi": row.get("total_emi"),
                "gst": row.get("gst"),
                "emi_financing": row.get("emi_financing"),
                "status": row.get("status"),
                "ex_showroom_amount": row.get("ex_showroom_amount"),
                "finance_emi_road_tax": row.get("finance_emi_road_tax"),
                "finance_hod_status": row.get("finance_hod_status"),
            })

            # car_quotation_item.insert()

        return {"car_quotation_item":car_quotation_item}
        # frappe.db.commit()
        # return f"File processed successfully: {file_path}"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "File Processing Error")
        frappe.throw(f"An error occurred while processing the file: {str(e)}")


@frappe.whitelist()
def generate_deduction(quotation_id):

    quotation = frappe.get_doc("Car Quotation", quotation_id)

    doc = frappe.new_doc("Company and Employee Deduction")

    doc.finance_quotation_id = quotation.name
    doc.employee_details = quotation.employee_details
    doc.finance_company = quotation.finance_company

    # Company values
    doc.quarterly_payment = quotation.quarterly_payment

    # Employee values
    doc.employee_quarterly_payment = quotation.employee_quarterly_payment

    # copy other required calculation fields
    doc.interest_rate = quotation.interest_rate
    doc.tenure = quotation.tenure
    doc.ex_showroom_amount_net_of_discount = quotation.ex_showroom_amount_net_of_discount
    doc.registration_charges = quotation.registration_charges
    doc.residual_value = quotation.residual_value

    doc.insert(ignore_permissions=True)

    return doc.name


def pmt(rate, nper, pv, fv=0, when=1):
    if rate == 0:
        return -(pv + fv) / nper
    return -(rate * (fv + pv * (1 + rate) ** nper)) / ((1 + rate * when) * ((1 + rate) ** nper - 1))


@frappe.whitelist()
def preview_deduction(quotation_id):

    q = frappe.get_doc("Car Quotation", quotation_id)
    employee = frappe.get_doc("Employee Master", q.employee_details)
    
    # ---- Company contribution logic (same as calculate_emi) ----

    interest_rate = flt(q.interest_rate) / 100
    tenure = flt(q.tenure)

    registration = flt(q.registration_charges)
    gst = flt(q.gst)

    insurance = flt(q.insurance)
    fms = flt(q.fleet_management_repairs_and_tyres)
    assist = flt(q.get("24x7_assist"))
    print("Value of 24x7 assist:",assist)
    # assist = flt(97)
    pickup = flt(q.pickup_and_drop)
    relief = flt(q.std_relief_car_non_accdt)
    monthly_rate = interest_rate / 12

    company_ex_showroom_amount_net_of_discount = flt(employee.eligibility)
    print("Company ex-showroom amount net of discount:", company_ex_showroom_amount_net_of_discount)

    registration = flt(q.registration_charges)

    # Company financed amount
    financed_amount = company_ex_showroom_amount_net_of_discount + registration
    print("Company financed amount:", financed_amount)

    # Residual value calculation (53%)
    residual_percent = flt(q.residual_value_percent) / 100
    residual_amount = flt(q.residual_value)

    pmt_val = pmt(monthly_rate, tenure, -financed_amount, residual_amount, 1)
    print("PMT for company:", pmt_val)

    gst_per_month = gst / tenure if tenure else 0

    emi_financing = round(pmt_val - gst_per_month)
    print("EMI financing for company:", emi_financing)

    finance_emi_road_tax = round(emi_financing - (registration / tenure if tenure else 0))
    print("Finance EMI road tax for company:", finance_emi_road_tax)

    gst_and_cess = round(finance_emi_road_tax * 45 / 100)
    print("GST and cess for company:", gst_and_cess)

    gst_on_fms = round((insurance + fms + assist + pickup + relief) * 18 / 100)
    print("GST on FMS for company:", gst_on_fms)
    print("Insurance for company:", insurance)
    print("FMS for company:", fms)
    print("Assist for company:", assist)

    total_emi1 = (
        emi_financing
        + gst_and_cess
        + insurance
        + fms
        + assist
        + pickup
        + relief
        + gst_on_fms
    )

    total_emi = round(total_emi1)
    print("Total EMI for company:", total_emi)

    quarterly_payment = math.ceil(total_emi * 3)
    interim_payment = math.ceil(quarterly_payment * 39 / 90)

    # ---- Employee contribution logic (same as calculate_employee_fields) ----

    employee_ex_showroom_amount_net_of_discount = (flt(q.ex_showroom_amount_net_of_discount) - company_ex_showroom_amount_net_of_discount)

    employee_financed_amount = math.ceil(employee_ex_showroom_amount_net_of_discount)

    pmt_emp = pmt(monthly_rate, tenure, -employee_financed_amount, 0, 1)
    print("PMT for employee:", pmt_emp)

    employee_emi_financing = pmt_emp

    employee_finance_emi_road_tax = employee_emi_financing
    print("Finance EMI road tax for employee:", employee_finance_emi_road_tax)

    employee_gst_and_cess = round(employee_finance_emi_road_tax * 45 / 100)
    print("GST and cess for employee:", employee_gst_and_cess)

    employee_total_emi = round(employee_emi_financing + employee_gst_and_cess)
    print("Total EMI for employee:", employee_total_emi)

    employee_quarterly_payment = math.ceil(employee_total_emi * 3)
    employee_interim_payment = math.ceil(employee_quarterly_payment * 39 / 90)

    return {
        # company
        "company_ex_showroom": company_ex_showroom_amount_net_of_discount,
        "company_financed_amount": financed_amount,
        "company_emi_financing": emi_financing,
        "company_finance_emi_road_tax": finance_emi_road_tax,
        "company_gst_and_cess": gst_and_cess,
        "company_gst_on_fms": gst_on_fms,
        "total_emi": total_emi,
        "quarterly_payment": quarterly_payment,
        "interim_payment": interim_payment,

        # employee
        "employee_ex_showroom": employee_ex_showroom_amount_net_of_discount,
        "employee_financed_amount": employee_financed_amount,
        "employee_emi_financing": employee_emi_financing,
        "employee_finance_emi_road_tax": employee_finance_emi_road_tax,
        "employee_gst_and_cess": employee_gst_and_cess,
        "employee_total_emi": employee_total_emi,
        "employee_quarterly_payment": employee_quarterly_payment,
        "employee_interim_payment": employee_interim_payment
    }

@frappe.whitelist()
def create_deduction_doc(quotation_id):

    q = frappe.get_doc("Car Quotation", quotation_id)
    values = preview_deduction(quotation_id)

    doc = frappe.new_doc("Company and Employee Deduction")

    doc.finance_quotation_id = quotation_id
    doc.employee_name = q.employee_details

    # company
    doc.ex_showroom_amount = values["company_ex_showroom"]
    doc.financed_amount = values["company_financed_amount"]
    doc.emi_financing = values["company_emi_financing"]
    doc.finance_emi_road_tax = values["company_finance_emi_road_tax"]
    doc.gst_and_cess = values["company_gst_and_cess"]
    doc.gst_on_fms = values["company_gst_on_fms"]

    doc.total_emi = values["total_emi"]
    doc.quarterly_payment = values["quarterly_payment"]
    doc.interim_payment = values["interim_payment"]

    # employee
    doc.employee_ex_showroom_amount_net_of_discount = values["employee_ex_showroom"]
    doc.employee_financed_amount = values["employee_financed_amount"]
    doc.employee_emi_financing = values["employee_emi_financing"]
    doc.employee_finance_emi_road_tax = values["employee_finance_emi_road_tax"]
    doc.employee_gst_and_cess = values["employee_gst_and_cess"]
    doc.employee_total_emi = values["employee_total_emi"]
    doc.employee_quarterly_payment = values["employee_quarterly_payment"]
    doc.employee_interim_payment = values["employee_interim_payment"]

    doc.insert(ignore_permissions=True)

    return doc.name


@frappe.whitelist()
def process_workflow(quotation_id, action, remarks=None):
    """
    Central workflow handler
    Handles:
    - Role validation
    - Status updates
    - Email triggers
    - Duplicate protection
    """

    user = frappe.session.user

    # Get role from your existing method
    role = frappe.get_attr(
        "alms_app.crms.doctype.car_indent_form.car_indent_form.management"
    )(current_frappe_user=user)

    role = (role or "").lower()
    print(f"User: {user}, Role: {role}, Action: {action}")

    doc = frappe.get_doc("Car Quotation", quotation_id)

    if action == "Approved":

        existing = frappe.db.exists(
            "Car Quotation",
            {
                "employee_details": doc.employee_details,
                "status": "Approved",
                "name": ["!=", doc.name]  # exclude current record
            }
        )

        if existing:
            frappe.throw("Quotation already approved for this Purchase Form")

    email_type = None

    # ============================
    # NORMALIZE ADMIN ROLE
    # ============================
    if role == "administrator":
        if doc.finance_team_status in ["", None, "Pending"]:
            role = "finance team"

        elif doc.finance_team_status == "Approved":
            role = "finance head"

        elif doc.finance_team_status == "Rejected":
            frappe.throw("Finance Team has already rejected this quotation")

    # Prevent double action
    if role == "finance team" and doc.finance_team_status in ["Approved", "Rejected"]:
        frappe.throw("Finance Team already acted on this quotation")

    if role == "finance head" and doc.finance_head_status in ["Approved", "Rejected"]:
        frappe.throw("Finance Head already acted on this quotation")

    # Dependency check
    if role == "finance head" and doc.finance_team_status != "Approved":
        frappe.throw("Finance Team must approve first")

    # ============================
    # FINANCE TEAM
    # ============================
    if role == "finance team":

        doc.finance_team_status = action
        doc.finance_team_remarks = remarks
        doc.finance_team_action_by = user

        if action == "Approved":
            email_type = "FinanceTeam To FinanceHead Payload"
        else:
            email_type = "Reject FinanceTeam to Vendor"

    # ============================
    # FINANCE HEAD
    # ============================
    elif role == "finance head":

        doc.finance_head_status = action
        doc.finance_head_remarks = remarks
        doc.finance_head_action_by = user

        if action == "Approved":
            email_type = "FinanceHead To AccountsTeam"

            # Reject all other quotations
            reject_other_quotations(doc)

        else:
            email_type = "Reject FinanceHead to FinanceTeam"

    else:
        frappe.throw(f"Not allowed. Role: {role}")

    # update_final_status(doc)
    doc.sync_status()
    doc.save(ignore_permissions=True)
    handle_no_approved_case(doc)

    # ============================
    # EMAIL (ONLY ONCE HERE)
    # ============================
    if email_type:
        frappe.logger().info(f"EMAIL TRIGGER → {email_type}")
        email_sender(
            name=doc.employee_details,
            email_send_to=email_type,
            payload={
                "quotation_id": doc.name
            }
        )

    return {"status": "success"}


def reject_other_quotations(doc):
    others = frappe.get_all(
        "Car Quotation",
        filters={
            "employee_details": doc.employee_details,
            "name": ["!=", doc.name]
        },
        pluck="name"
    )

    for q in others:
        q_doc = frappe.get_doc("Car Quotation", q)

        if q_doc.status == "Rejected":
            continue

        q_doc.finance_team_status = "Rejected"
        q_doc.finance_head_status = "Rejected"

        q_doc.status = "Rejected"

        q_doc.save(ignore_permissions=True)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_available_purchase_forms(doctype, txt, searchfield, start, page_len, filters):

    # Step 1: Approved Purchase Forms
    purchase_forms = frappe.get_all(
        "Purchase Team Form",
        filters={"status": "Approved"},
        pluck="name"
    )

    # Step 2: Already used (Approved quotation exists)
    used_forms = frappe.get_all(
        "Car Quotation",
        filters={"status": "Approved"},
        pluck="employee_details"
    )

    # Step 3: Remove used ones
    available = list(set(purchase_forms) - set(used_forms))

    # Step 4: Apply search filter (VERY IMPORTANT for typing in link field)
    if txt:
        available = [pf for pf in available if txt.lower() in pf.lower()]

    # Step 5: Return as list of tuples (Frappe expects this)
    return [(pf,) for pf in available[start:start + page_len]]


def update_final_status(doc):
    ft = (doc.finance_team_status or "").strip().lower()
    fh = (doc.finance_head_status or "").strip().lower()

    # Normalize values
    pending_values = ["", "-select-", "pending"]

    # Rejection overrides everything
    if ft == "rejected" or fh == "rejected":
        doc.status = "Rejected"
        return

    # Fully approved
    if ft == "approved" and fh == "approved":
        doc.status = "Approved"
        return

    # Everything else
    doc.status = "Pending"


@frappe.whitelist()
def get_quotation_timeline(root_id):

    quotations = frappe.get_all(
        "Car Quotation",
        filters={"root_quotation": root_id},
        fields=[
            "name",
            "parent_quotation",
            "version_number",
            "status",
            "finance_company",
            "creation"
        ],
        order_by="version_number asc"
    )

    return quotations

@frappe.whitelist()
def create_revised_quotation(old_id):

    old = frappe.get_doc("Car Quotation", old_id)

    new_doc = frappe.copy_doc(old)

    new_doc.quotation_status = "Revised"
    new_doc.revised_modify_quotation_id = old.name

    new_doc.insert(ignore_permissions=True)

    return new_doc.name