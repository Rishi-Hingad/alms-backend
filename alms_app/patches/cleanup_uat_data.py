import frappe

def execute():
    # 1. Clean up corrupt Setup Wizard data
    frappe.db.sql("""
        DELETE FROM `tabInstalled Application` 
        WHERE parent IS NULL OR parent = ''
    """)
    
    # 2. Update old Dashboard references for 'ALMS Employee' -> 'Employee'
    frappe.db.sql("""
        UPDATE `tabWorkspace Quick List` 
        SET document_type='Employee' 
        WHERE document_type='ALMS Employee'
    """)
    
    frappe.db.sql("""
        UPDATE `tabNumber Card` 
        SET document_type='Employee' 
        WHERE document_type='ALMS Employee'
    """)
    
    frappe.db.sql("""
        UPDATE `tabDashboard Chart` 
        SET document_type='Employee' 
        WHERE document_type='ALMS Employee'
    """)
    
    frappe.db.sql("""
        UPDATE `tabCustom HTML Block` 
        SET html = REPLACE(html, 'ALMS Employee', 'Employee'), 
            script = REPLACE(script, 'ALMS Employee', 'Employee')
    """)
    
    frappe.db.sql("""
        UPDATE `tabNumber Card` 
        SET filters_json = REPLACE(filters_json, 'ALMS Employee', 'Employee'), 
            dynamic_filters_json = REPLACE(dynamic_filters_json, 'ALMS Employee', 'Employee'), 
            filters_config = REPLACE(filters_config, 'ALMS Employee', 'Employee')
    """)
    
    frappe.db.sql("""
        UPDATE `tabWorkspace Quick List` 
        SET quick_list_filter = REPLACE(quick_list_filter, 'ALMS Employee', 'Employee')
    """)
    
    frappe.db.sql("""
        UPDATE `tabDashboard Chart` 
        SET filters_json = REPLACE(filters_json, 'ALMS Employee', 'Employee'), 
            dynamic_filters_json = REPLACE(dynamic_filters_json, 'ALMS Employee', 'Employee')
    """)

    frappe.db.commit()
