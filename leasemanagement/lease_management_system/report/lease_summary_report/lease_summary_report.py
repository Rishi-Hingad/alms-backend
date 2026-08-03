import math
from datetime import date, datetime
import frappe
from frappe import _
from frappe.desk.query_report import run
from frappe.utils import getdate

def execute(filters=None):
        if not filters:
                return [], []

        company_name = filters.get("company_name")

        if not company_name:
                frappe.throw(_("Please select a Company."))

        data = []
        columns = [
                {"label": _("Lease"), "fieldname": "lease_id", "fieldtype": "Data", "width": 120},
                {"label": _("Vendor"), "fieldname": "vendor", "fieldtype": "Data", "width": 120},
                {
                        "label": _("Asset Description"),
                        "fieldname": "asset_description",
                        "fieldtype": "Data",
                        "width": 150,
                },
                {
                        "label": _("Opening ROU Asset"),
                        "fieldname": "rou_opening",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
                {
                        "label": _("Closing ROU Asset"),
                        "fieldname": "rou_closing",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
                {
                        "label": _("Opening Liability"),
                        "fieldname": "liability_opening",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
                {
                        "label": _("Closing Liability"),
                        "fieldname": "liability_closing",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
                {
                        "label": _("Rent Paid"),
                        "fieldname": "rent_paid",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
                {
                        "label": _("Interest Expense"),
                        "fieldname": "interest_expense",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
                {
                        "label": _("Depreciation"),
                        "fieldname": "depreciation",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
                {
                        "label": _("Additions - ROU Asset"),
                        "fieldname": "additions_rou_asset",
                        "fieldtype": "Currency",
                        "width": 120,
                        "precision": 2,
                },
                {
                        "label": _("Additions - Lease Liability"),
                        "fieldname": "additions_lease_liability",
                        "fieldtype": "Currency",
                        "width": 120,
                        "precision": 2,
                },
                {
                        "label": _("Check (ROU)"),
                        "fieldname": "check_rou",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
                {
                        "label": _("Check (Liability)"),
                        "fieldname": "check_liability",
                        "fieldtype": "Currency",
                        "width": 200,
                        "precision": 2,
                },
        ]

        fin_start_year = filters.get("fin_start_year")
        fin_end_year = filters.get("fin_end_year")
        leases = frappe.get_all(
                "Lease Management",
                order_by="name asc",
                filters={
                        "Company": company_name,
                },
                fields=["name"],
        )

        grand_total_opening_rou = 0
        grand_total_closing_rou = 0
        grand_total_opening_liability = 0
        grand_total_closing_liability = 0
        grand_total_rent_paid = 0
        grand_total_interest_expense = 0
        grand_total_depreciation = 0

        for lease in leases:
                lease_doc = frappe.get_doc("Lease Management", lease.name)
                if lease_doc.type_of_asset == "Immovable":
                        prop_doc = frappe.get_doc("Property Master", lease_doc.property_description)
                else:
                        car_desc = frappe.get_doc("Vehicle Details", lease_doc.car_description)

                msdate = date(int(fin_start_year), 4, 1)
                medate = date(int(fin_end_year), 3, 1)

                lease_end = None
                if lease_doc.agreement_end_date:
                        lease_end = datetime.strptime(str(lease_doc.agreement_end_date), "%Y-%m-%d").date()

                if lease_end and lease_end < msdate:
                        continue

                if lease_doc.calculation_rate_type == "Daily Rate" and lease_doc.lease_period == "Long Term (Greater Than 12 Months)":
                        lreport = "Lease Report"
                else:
                        lreport = "Lease Report Monthly (With Escalation)"
                result = run(lreport, filters={"docname": lease.name})
                rows = result.get("result", [])

                sdate = date(int(fin_start_year), 3, 31)
                edate = date(int(fin_end_year), 3, 31)
                
                def parse_date(d):
                        if not d: return None
                        if isinstance(d, date): return d
                        if isinstance(d, datetime): return d.date()
                        try:
                                return getdate(d)
                        except Exception:
                                return None

                opening_rou = 0
                opening_liability = 0
                closing_rou = 0
                closing_liability = 0
                
                for r in rows:
                        rmonth_end = parse_date(r.get("month_end_date"))
                        if rmonth_end == sdate:
                                opening_rou = r.get("wdv", 0)
                                opening_liability = r.get("closing_liability", 0)
                        if rmonth_end == edate:
                                closing_rou = r.get("wdv", 0)
                                closing_liability = r.get("closing_liability", 0)
                                
                mlp_list, interest_list, depreciation_list = [], [], []
                
                for r in rows:
                        rmonth_start = parse_date(r.get("month_start_date"))
                        if rmonth_start and rmonth_start >= msdate and rmonth_start <= medate:
                                mlp_list.append(r.get("mlp", 0))
                                interest_list.append(r.get("interest_cost", 0))
                                depreciation_list.append(r.get("depreciation", 0))

                if opening_rou == 0:
                        additions_rou_asset = rows[0].get("wdv", 0) if rows else 0
                        additions_lease_lia = additions_rou_asset
                else:
                        additions_rou_asset = additions_lease_lia = 0

                total_rent_paid = 0
                total_interest_cost = 0
                total_depreciation = 0

                for i in range(len(mlp_list)):
                        val = mlp_list[i]
                        if isinstance(val, (int, float)) and not math.isnan(float(val)):
                                total_rent_paid += val
                                
                        val_int = interest_list[i]
                        if isinstance(val_int, (int, float)) and not math.isnan(float(val_int)):
                                total_interest_cost += val_int
                                
                        val_dep = depreciation_list[i]
                        if isinstance(val_dep, (int, float)) and not math.isnan(float(val_dep)):
                                total_depreciation += val_dep

                rou_check = opening_rou - total_depreciation - closing_rou + additions_rou_asset
                liability_check = (
                        opening_liability
                        + total_interest_cost
                        - total_rent_paid
                        - closing_liability
                        + additions_rou_asset
                )
                grand_total_opening_rou += opening_rou
                grand_total_closing_rou += closing_rou
                grand_total_opening_liability += opening_liability
                grand_total_closing_liability += closing_liability
                grand_total_rent_paid += total_rent_paid
                grand_total_interest_expense += total_interest_cost
                grand_total_depreciation += total_depreciation

                if lease_doc.type_of_asset == "Immovable":
                        data.append(
                                {
                                        "lease_id": lease.name,
                                        "vendor": prop_doc.vendor,
                                        "asset_description": prop_doc.address,
                                        "rou_opening": opening_rou,
                                        "rou_closing": closing_rou,
                                        "liability_opening": opening_liability,
                                        "liability_closing": closing_liability,
                                        "rent_paid": total_rent_paid,
                                        "interest_expense": total_interest_cost,
                                        "depreciation": total_depreciation,
                                        "additions_rou_asset": additions_rou_asset,
                                        "additions_lease_liability": additions_lease_lia,
                                        "check_rou": rou_check,
                                        "check_liability": liability_check,
                                }
                        )
                else:
                        data.append(
                                {
                                        "lease_id": lease.name,
                                        "vendor": car_desc.vendor,
                                        "asset_description": car_desc.employee_name,
                                        "rou_opening": opening_rou,
                                        "rou_closing": closing_rou,
                                        "liability_opening": opening_liability,
                                        "liability_closing": closing_liability,
                                        "rent_paid": total_rent_paid,
                                        "interest_expense": total_interest_cost,
                                        "depreciation": total_depreciation,
                                        "additions_rou_asset": additions_rou_asset,
                                        "additions_lease_liability": additions_lease_lia,
                                        "check_rou": rou_check,
                                        "check_liability": liability_check,
                                }
                        )
        data.append(
                {
                        "lease_id": "",
                        "vendor": "",
                        "asset_description": "",
                        "rou_opening": grand_total_opening_rou,
                        "rou_closing": grand_total_closing_rou,
                        "liability_opening": grand_total_opening_liability,
                        "liability_closing": grand_total_closing_liability,
                        "rent_paid": grand_total_rent_paid,
                        "interest_expense": grand_total_interest_expense,
                        "depreciation": grand_total_depreciation,
                        "additions_rou_asset": "",
                        "additions_lease_liability": "",
                        "check_rou": "",
                        "check_liability": "",
                }
        )

        return columns, data
