import frappe

def run():
    print('Checking Workflows for Purchase Form...')
    wfs = frappe.get_all('Workflow', filters={'document_type': 'Purchase Form'}, fields=['name', 'is_active'])
    print(wfs)

