import frappe

def update_doctype():
    fields = [
        {'fieldname': 'approval_timline_tab', 'fieldtype': 'Tab Break', 'label': 'Approval Timline'},
        {'fieldname': 'approval_section', 'fieldtype': 'Section Break', 'label': 'Approval'},
        {'fieldname': 'is_submitted', 'fieldtype': 'Check', 'label': 'Is Submitted', 'hidden': 1, 'read_only': 1, 'default': '0'},
        {'fieldname': 'approval_initiated', 'fieldtype': 'Check', 'label': 'Approval Initiated', 'hidden': 1, 'read_only': 1, 'default': '0'},
        {'fieldname': 'approval_entry', 'fieldtype': 'Link', 'label': 'Approval Entry', 'options': 'Approval Entry', 'hidden': 1, 'read_only': 1},
        {'fieldname': 'approval_token', 'fieldtype': 'Data', 'label': 'Approval Token', 'hidden': 1},
        {'fieldname': 'trail_section', 'fieldtype': 'Section Break', 'label': 'Trail'},
        {'fieldname': 'approval_trail_html', 'fieldtype': 'HTML', 'label': 'Approval Trail'}
    ]

    doc = frappe.get_doc('DocType', 'Purchase Team Form')
    existing_fields = [f.fieldname for f in doc.fields]
    changed = False
    for f in fields:
        if f['fieldname'] not in existing_fields:
            doc.append('fields', {
                'fieldname': f['fieldname'],
                'fieldtype': f['fieldtype'],
                'label': f['label'],
                'hidden': f.get('hidden', 0),
                'read_only': f.get('read_only', 0),
                'default': f.get('default'),
                'options': f.get('options')
            })
            changed = True

    if changed:
        doc.save()
        frappe.db.commit()
        print('Fields added successfully!')
    else:
        print('Fields already exist.')
