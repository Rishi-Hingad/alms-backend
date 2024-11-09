# quotation_chart.py

import frappe
from frappe import _

def get_finance_company_status_chart():
    # Fetch data from the Car Quotation doctype
    data = frappe.db.sql("""
        SELECT finance_company, status, COUNT(*) as count
        FROM `tabCar Quotation`
        WHERE finance_company IN ('Easy Assets', 'ALD', 'XYZ') AND status IN ('Approved', 'Rejected')
        GROUP BY finance_company, status
    """, as_dict=True)

    # Define chart data structure
    chart_data = {
        "labels": ["Approved", "Rejected"],
        "datasets": [
            {
                "name": "Easy Assets",
                "values": [0, 0],  # Default values for Approved and Rejected
                "color": "#0000FF"  # Blue color for Easy Assets
            },
            {
                "name": "ALD",
                "values": [0, 0],
                "color": "#FF0000"  # Red color for ALD
            },
            {
                "name": "XYZ",
                "values": [0, 0],
                "color": "#00FF00"  # Green color for XYZ
            }
        ]
    }

    # Map data from SQL results to chart data structure
    for entry in data:
        finance_company = entry['finance_company']
        status = entry['status']
        count = entry['count']

        # Find the correct dataset and update values
        if finance_company == "Easy Assets":
            chart_data["datasets"][0]["values"][0 if status == "Approved" else 1] = count
        elif finance_company == "ALD":
            chart_data["datasets"][1]["values"][0 if status == "Approved" else 1] = count
        elif finance_company == "XYZ":
            chart_data["datasets"][2]["values"][0 if status == "Approved" else 1] = count

    # Prepare chart settings
    chart_config = {
        "data": chart_data,
        "type": "bar",
        "title": _("Quotation Status by Finance Company"),
        "axisOptions": {"xIsSeries": 1},
    }
    
    return chart_config
