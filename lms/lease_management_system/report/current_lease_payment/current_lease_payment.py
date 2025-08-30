# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

def execute(filters=None):
    data=[]
    columns = [
        {"label": "Lease", "fieldname": "lease", "fieldtype": "Data", "width": 150},
        {"label": "Month Start Date", "fieldname": "month_start_date", "fieldtype": "Date", "width": 150},
        {"label": "Month End Date", "fieldname": "month_end_date", "fieldtype": "Date", "width": 150},
        {"label": "Total Rent", "fieldname": "total_rent", "fieldtype": "Currency", "width": 200},
        {"label": "Payment Status", "fieldname": "payement_status", "fieldtype": "Data", "width": 200}
    ]

    today = frappe.utils.nowdate()
    if isinstance(today, str):
        today = datetime.strptime(today, "%Y-%m-%d")
        
    current_month = today.strftime("%Y-%m")
    lease_status="Pending"
    ms_date=None
    me_date=None
        
    leases = frappe.get_all(
        "Lease Management",
        filters={
            "agreement_start_date": ("<=", today),
            "agreement_end_date": (">=", today)
        },
        order_by="name asc",
        fields=["name"]
    )
    for lease in leases:
        lease_doc=frappe.get_doc("Lease Management",lease.name)
        timeline=lease_doc.get_lease_rent_timeline()
        mdata=lease_doc.get_lease_monthly_data()
        lease_data=mdata.get(current_month,0)
        inv_attachment=lease_doc.get_invoice_attachments_with_dates()
        ms_date=lease_data[0]
        me_date=lease_data[1]
        rent=timeline.get(current_month,0)
        inv_dates=[]
        for i in range(len(inv_attachment)):
            record=inv_attachment[i]
            inv_dates.append(record["uploaded_on"])

        for r in lease_doc.invoice_details:
            # inv_date=r.invoice_date
            for i in range(len(inv_dates)):
                if inv_dates[i].strftime("%Y-%m") and (r.to_date.strftime("%Y-%m")==current_month or r.from_date.strftime("%Y-%m")==current_month):
                    lease_status="Paid on "+str(inv_dates[i])
                    break
            # if inv_date.strftime("%Y-%m")==current_month:
            #     lease_status="Paid on "+str(inv_date)
            else:
                if today.date()>me_date:
                    lease_status="Was Due on "+str(me_date)
        data.append({"lease":lease.name,"month_start_date": ms_date,"month_end_date": me_date,"total_rent": rent,"payement_status":lease_status})
        lease_status="Pending"
    
    return columns,data
