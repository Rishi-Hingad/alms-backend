# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from dateutil.relativedelta import relativedelta


def execute(filters=None):
    columns = [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
        {"label": "Total Rent", "fieldname": "total_rent", "fieldtype": "Currency", "width": 150,"precision":4}
    ]

    today = frappe.utils.nowdate()
    if isinstance(today, str):
        today = datetime.strptime(today, "%Y-%m-%d")

    current_month = today.strftime("%Y-%m")
    previous_month = (today - relativedelta(months=1)).strftime("%Y-%m")
    next_month = (today + relativedelta(months=1)).strftime("%Y-%m")

    leases = frappe.get_all(
        "Lease Management",
        filters={
            "agreement_start_date": ("<=", today),
            "agreement_end_date": (">=", today)
        },
        fields=["name"]
    )

    monthly_totals = {
        "Previous Month": 0.0,
        "Current Month": 0.0,
        "Next Month": 0.0
    }

    for lease in leases:
        lease_doc = frappe.get_doc("Lease Management", lease.name)
        timeline_l = lease_doc.get_lease_rent_timeline()

        monthly_totals["Previous Month"] += timeline_l.get(previous_month, 0)
        monthly_totals["Current Month"] += timeline_l.get(current_month, 0)
        monthly_totals["Next Month"] += timeline_l.get(next_month, 0)

    # Prepare rows
    data = []
    for month, total in monthly_totals.items():
        if month=="Previous Month":
            month=(today - relativedelta(months=1)).strftime("%B %Y")
        elif month=="Current Month":
            month=today.strftime("%B %Y")
        elif month=="Next Month":
            month=(today + relativedelta(months=1)).strftime("%B %Y")
        data.append({"month": month, "total_rent": total})

    return columns, data
