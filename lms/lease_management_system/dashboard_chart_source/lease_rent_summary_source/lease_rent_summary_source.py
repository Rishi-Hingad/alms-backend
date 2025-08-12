import frappe
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta


@frappe.whitelist()
def get():
    return {
        "labels": ["Previous Month", "Current Month", "Next Month"],
        "datasets": [
            {
                "name": "Sample Data",
                "values": [1000, 2000, 3000]
            }
        ],
        "type": "bar"
    }


# @frappe.whitelist()
# def get():
#     today = frappe.utils.nowdate()
#     if isinstance(today, str):
#         today = datetime.strptime(today, "%Y-%m-%d")

#     current_month = today.strftime("%Y-%m")
#     previous_month = (today - relativedelta(months=1)).strftime("%Y-%m")
#     next_month = (today + relativedelta(months=1)).strftime("%Y-%m")

#     leases = frappe.get_all(
#         "Lease Management",
#         filters={
#             "agreement_start_date": ("<=", today),
#             "agreement_end_date": (">=", today)
#         },
#         fields=["name"]
#     )

#     monthly_totals = {
#         "Previous Month": 0.0,
#         "Current Month": 0.0,
#         "Next Month": 0.0
#     }

#     for lease in leases:
#         lease_doc = frappe.get_doc("Lease Management", lease.name)
#         timeline_l = lease_doc.get_lease_rent_timeline()

#         monthly_totals["Previous Month"] += timeline_l.get(previous_month, 0)
#         monthly_totals["Current Month"] += timeline_l.get(current_month, 0)
#         monthly_totals["Next Month"] += timeline_l.get(next_month, 0)

#     return {
#         "labels": list(monthly_totals.keys()),
#         "datasets": [
#             {"name": "Lease Rent", "values": list(monthly_totals.values())}
#         ],
#         "type": "bar"
#     }



# def get_config(name):
# 	today = frappe.utils.nowdate()
# 	if isinstance(today, str):
# 		today = datetime.strptime(today, "%Y-%m-%d")

# 	current_month = today.strftime("%Y-%m")
# 	previous_month = (today - relativedelta(months=1)).strftime("%Y-%m")
# 	next_month = (today + relativedelta(months=1)).strftime("%Y-%m")

# 	leases = frappe.get_all("Lease Management",
# 		filters={
# 			"agreement_start_date": ("<=", today),
# 			"agreement_end_date": (">=", today)
# 		},
# 		fields=["name"]
# 	)

# 	monthly_totals = {
# 		"Previous Month": 0.0,
# 		"Current Month": 0.0,
# 		"Next Month": 0.0
# 	}

# 	for lease in leases:
# 		lease_doc = frappe.get_doc("Lease Management", lease.name)
# 		timeline = lease_doc.get_lease_rent_timeline()

# 		monthly_totals["Previous Month"] += timeline.get(previous_month, 0)
# 		monthly_totals["Current Month"] += timeline.get(current_month, 0)
# 		monthly_totals["Next Month"] += timeline.get(next_month, 0)

# 	return {
# 		"labels": ["Previous Month", "Current Month", "Next Month"],
# 		"datasets": [
# 			{
# 				"name": "Lease Rent Summary",
# 				"values": [
# 					round(monthly_totals["Previous Month"], 2),
# 					round(monthly_totals["Current Month"], 2),
# 					round(monthly_totals["Next Month"], 2)
# 				]
# 			}
# 		],
# 		"type": "bar",
# 		"colors": ["#56CC9D"]
# 	}