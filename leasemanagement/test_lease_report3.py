import frappe
from lease_management_system.report.lease_report.lease_report import execute
import alms_app.api.api_utils as api_utils

original_get_mlp = api_utils.get_mlp

def patched_get_mlp(*args, **kwargs):
    res = original_get_mlp(*args, **kwargs)
    current_date = args[8]
    if str(current_date)[0:7] == "2024-04":
        print(f"DEBUG get_mlp at {current_date} -> returns {res}")
    return res

api_utils.get_mlp = patched_get_mlp

def run_test():
    columns, rows = execute(filters={"docname": "LMS-APR22_MAR27-154"})
