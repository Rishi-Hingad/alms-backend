# Copyright (c) 2025, Shradha_Siddhi and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import monthrange

def execute(filters=None):
    data=[]
    columns = [
        {"label": "Lease", "fieldname": "lease", "fieldtype": "Data", "width": 200},
        {"label": "Month Start Date", "fieldname": "month_start_date", "fieldtype": "Date", "width": 150},
        {"label": "Month End Date", "fieldname": "month_end_date", "fieldtype": "Date", "width": 150},
        {"label": "Total Rent", "fieldname": "total_rent", "fieldtype": "Currency", "width": 200,"precision":4},
        {"label": "Payment Status", "fieldname": "payment_status", "fieldtype": "Data", "width": 200}
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
        # inv_attachment=lease_doc.get_invoice_attachments_with_dates()
        if not lease_data and not isinstance(lease_data,list):
            continue
        else:
            ms_date=lease_data[0]
            me_date=lease_data[1]
        rent=timeline.get(current_month,0)
        # inv_dates=[]
        # for i in range(len(inv_attachment)):
        #     record=inv_attachment[i]
        #     inv_dates.append(record["uploaded_on"])

        if len(lease_doc.invoice_details)>0:
            # for r in lease_doc.invoice_details:
            #     if r.payment_status=="Paid":
            #         lease_status="Paid"
            #         break
            # else:
            #     if today.date()>me_date:
            #         lease_status="Was Due on "+str(me_date)

            for child in lease_doc.invoice_details:
                from_date = child.from_date
                to_date = child.to_date
                date_ranges=[]
                current=from_date
                while current<=to_date:
                    start_date=current
                    _,last_day=monthrange(current.year, current.month)
                    end_date=datetime(current.year, current.month, last_day)

                    if end_date.date()>to_date:
                        end_date=to_date

                    # date_ranges.append(start_date.strftime("%Y-%m-%d"))
                    # date_ranges.append(end_date.strftime("%Y-%m-%d"))
                    if ms_date.strftime("%Y-%m-%d") == start_date.strftime("%Y-%m-%d") or me_date.strftime("%Y-%m-%d") == end_date.strftime("%Y-%m-%d"):
                        date_ranges.append([start_date.strftime("%Y-%m-%d"),end_date.strftime("%Y-%m-%d")])
                    
                    if current.month==12:
                        current=current.replace(year=current.year+1,month=1,day=1)
                    else:
                        current=current.replace(month=current.month+1,day=1)
                
                # frappe.msgprint(lease.name+"==="+str(date_ranges)+" len="+str(len(date_ranges)))
                if len(date_ranges)>0:
                    for i in range(len(date_ranges)):
                        rsdate,redate=date_ranges[i]
                        if ms_date.strftime("%Y-%m-%d") == rsdate or me_date.strftime("%Y-%m-%d") == redate:
                            # frappe.msgprint("Yes"+" "+child.payment_status+" || "+str())+" || "+str(me_date.strftime("%Y-%m-%d"))+" ** "+str(date_ranges[i]))
                            lease_status=child.payment_status
                            break
        else:
            # if today.date()>me_date:
            #         lease_status="Was Due on "+str(me_date)
            if today.date()>=me_date:
                lease_status="Due"
            else:
                lease_status="Pending"

        # for r in lease_doc.invoice_details:
        #     # inv_date=r.invoice_date
        #     for i in range(len(inv_dates)):
        #         if r.payment_status=="Paid":
        #             # lease_status="Paid on "+str(inv_dates[i])
        #             lease_status="Paid"
        #             break
        #         # if inv_dates[i].strftime("%Y-%m") and (r.to_date.strftime("%Y-%m")==current_month or r.from_date.strftime("%Y-%m")==current_month):
        #         #     lease_status="Paid on "+str(inv_dates[i])
        #         #     break
        #     # if inv_date.strftime("%Y-%m")==current_month:
        #     #     lease_status="Paid on "+str(inv_date)
        #     else:
        #         if today.date()>me_date:
        #             lease_status="Was Due on "+str(me_date)
        if rent is not None and lease_status=="":
            if today.date()>=me_date:
                lease_status="Due"
            else:
                lease_status="Pending"

        data.append({"lease":lease.name,"month_start_date": ms_date,"month_end_date": me_date,"total_rent": rent,"payment_status":lease_status})
        lease_status="Pending"
    
    return columns,data
