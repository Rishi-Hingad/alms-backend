import frappe
from alms_app.approval.approval_router import trigger_approval_if_matrix_exists

def run():
    print('Testing trigger on latest Purchase Form...')
    docs = frappe.get_all('Purchase Form', fields=['name', 'is_submitted', 'approval_initiated', 'docstatus'], limit=1, order_by='modified desc')
    if not docs:
        print('No purchase form found.')
        return
    doc = frappe.get_doc('Purchase Form', docs[0].name)
    print(f'Doc: {doc.name}, is_submitted: {doc.is_submitted}, approval_initiated: {doc.get("approval_initiated")}')
    
    # Force it
    doc.is_submitted = 1
    doc.approval_initiated = 0
    
    print('Calling trigger_approval_if_matrix_exists...')
    try:
        trigger_approval_if_matrix_exists(doc)
        print('Success.')
    except Exception as e:
        print('Error:', e)
        print(frappe.get_traceback())
