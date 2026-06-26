import frappe

def run():
    print('Checking Stages for AP-000002 (Purchase Form)...')
    m = frappe.get_doc('Approval Matrix', 'AP-000002')
    stages = getattr(m, 'stages', getattr(m, 'approval_stages', []))
    print(f'Found {len(stages)} stages.')
    for s in stages:
        print(getattr(s, 'approval_stage', getattr(s, 'stage_number', None)), getattr(s, 'employee', None), getattr(s, 'role', None), getattr(s, 'team', None))

