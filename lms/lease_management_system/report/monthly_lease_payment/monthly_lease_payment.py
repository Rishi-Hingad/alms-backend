# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

def execute(filters=None):
    if not filters:
        return [],[]
    month=filters.get("month")
    year=filters.get("year")
    month_int=datetime.strptime(month, "%B").month
    m=str(month_int).zfill(2)
    month_year=str(year)+"-"+str(m)
    
    data=[]
    columns = [
        {"label": "Lease", "fieldname": "lease", "fieldtype": "Data", "width": 150},
        {"label": "Month Start Date", "fieldname": "month_start_date", "fieldtype": "Date", "width": 150},
        {"label": "Month End Date", "fieldname": "month_end_date", "fieldtype": "Date", "width": 150},
        {"label": "Total Rent", "fieldname": "total_rent", "fieldtype": "Currency", "width": 150},
        {"label": "Payment Status", "fieldname": "payement_status", "fieldtype": "Data", "width": 200}
    ]

    lease_status="Pending"
    ms_date=None
    me_date=None
    today = frappe.utils.nowdate()
    if isinstance(today, str):
        today = datetime.strptime(today, "%Y-%m-%d")
        
    leases = frappe.get_all(
        "Lease Management",
        order_by="name asc",
        fields=["name"]
    )
    # month_year="2025-08"
    for lease in leases:
        lease_status=""
        lease_doc=frappe.get_doc("Lease Management",lease.name)
        timeline=lease_doc.get_lease_rent_timeline()
        mdata=lease_doc.get_lease_monthly_data()
        lease_data=mdata.get(month_year,0)
        if not lease_data and not isinstance(lease_data,list):
            continue
        else:
            ms_date=lease_data[0]
            me_date=lease_data[1]
            
        
        rent=timeline.get(month_year,0)
        if len(lease_doc.invoice_details)>0:
            for r in lease_doc.invoice_details:
                inv_date=r.invoice_date
                if inv_date.strftime("%Y-%m")==month_year:
                    lease_status="Paid on "+str(inv_date)
                    break
                else:
                    # lease_status=""
                    if today.date()>=me_date:
                        lease_status="Due"
                    else:
                        lease_status="Pending"  
        else:
            if today.date()>=me_date:
                lease_status="Due"
            else:
                lease_status="Pending"
                
        data.append({"lease":lease.name,"month_start_date": ms_date,"month_end_date": me_date,"total_rent": rent,"payement_status":lease_status})
    
    return columns,data

