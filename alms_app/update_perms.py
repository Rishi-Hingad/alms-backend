import json

def update_json(filepath, role, perms_dict):
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    perms = data.get('permissions', [])
    # Remove existing role if present
    perms = [p for p in perms if p.get('role') != role]
    
    # Add new role perms
    new_perm = {'role': role}
    new_perm.update(perms_dict)
    perms.append(new_perm)
    
    data['permissions'] = perms
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=1)

# Selected Vendor
update_json('apps/alms_app/alms_app/crms/doctype/selected_vendor/selected_vendor.json', 'Finance Team', {
   'read': 1, 'write': 1, 'create': 1, 'delete': 1,
   'email': 1, 'export': 1, 'print': 1, 'report': 1, 'share': 1
})

# Purchase Form
update_json('apps/alms_app/alms_app/crms/doctype/purchase_form/purchase_form.json', 'Finance Team', {
   'read': 1, 'write': 1, 'create': 0, 'delete': 0,
   'email': 1, 'export': 1, 'print': 1, 'report': 1, 'share': 1
})
