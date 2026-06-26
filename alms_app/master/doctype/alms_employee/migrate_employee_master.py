import frappe

def execute():
    print('Starting full migration using raw SQL...')
    try:
        records = frappe.db.sql('SELECT * FROM `tabEmployee Master`', as_dict=True)
    except Exception:
        print("tabEmployee Master not found. Skipping migration.")
        return

    migrated = 0
    created = 0
    for row in records:
        emp_code = row.get('employee_code')
        emp_email = row.get('email_id')
        emp_name = frappe.db.get_value('ALMS Employee', {'employee_code': emp_code}, 'name')
        if not emp_name and emp_email:
            emp_name = frappe.db.get_value('ALMS Employee', {'company_email': emp_email}, 'name')

        if emp_name:
            # Update existing
            update_data = {}
            if row.get('eligibility'):
                update_data['eligibility'] = row.get('eligibility')
            if row.get('status'):
                update_data['eligibility_email_status'] = row.get('status')
            if row.get('reporting_head'):
                update_data['reporting_head'] = row.get('reporting_head')
            
            if update_data:
                frappe.db.set_value('ALMS Employee', emp_name, update_data)
                migrated += 1
        else:
            # Create new via raw frappe.get_doc({...}).db_insert() to avoid validation
            try:
                parts = (row.get('employee_name') or '').split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
                
                new_emp_name = frappe.generate_hash()
                
                frappe.db.sql("""
                    INSERT INTO `tabEmployee` (
                        name, creation, modified, modified_by, owner, docstatus, 
                        employee_code, first_name, last_name, company_email, 
                        eligibility, eligibility_email_status, reporting_head, 
                        department, meril_designation, cell_number, 
                        date_of_joining, date_of_birth
                    ) VALUES (
                        %s, NOW(), NOW(), 'Administrator', 'Administrator', 0,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s
                    )
                """, (
                    new_emp_name, emp_code, first_name, last_name, emp_email,
                    row.get('eligibility'), row.get('status'), row.get('reporting_head'),
                    row.get('department'), row.get('designation'), row.get('contact_number'),
                    row.get('date_of_joining'), row.get('date_of_birth')
                ))
                created += 1
            except Exception as e:
                print(f'Error creating employee {emp_code} with SQL: {e}')
                
    frappe.db.commit()
    print(f'Done. Updated: {migrated}, Created: {created}')

