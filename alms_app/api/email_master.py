import frappe
import frappe.client

class EmailMaster:
    hr_user = frappe.get_all('Management Team', filters={'designation': 'HR'}, fields=['full_name', 'email_id'])[0]
    hr_team_email = hr_user.get("email_id")
    hr_team = hr_user.get("full_name")

    hr_head_user = frappe.get_all('Management Team', filters={'designation': 'HR Head'}, fields=['full_name', 'email_id'])[0]
    # hr_head_email = hr_user.get("email_id")
    hr_head_email = hr_head_user.get("email_id")
    hr_head = hr_head_user.get("full_name")
    
    purchase_user = frappe.get_all('Management Team', filters={'designation': 'Purchase'}, fields=['full_name', 'email_id'])[0]
    purchase_team_email = purchase_user.get("email_id")
    purchase_team = purchase_user.get("full_name")
    
    purchase_head_user = frappe.get_all('Management Team', filters={'designation': 'Purchase Head'}, fields=['full_name', 'email_id'])[0]
    purchase_head_email = purchase_head_user.get("email_id")
    purchase_head = purchase_head_user.get("full_name")
    
    finance_user = frappe.get_all('Management Team', filters={'designation': 'Finance'}, fields=['full_name', 'email_id'])[0]
    finance_team_email = finance_user.get("email_id")
    finance_team = finance_user.get("full_name")
    
    finance_head_user = frappe.get_all('Management Team', filters={'designation': 'Finance Head'}, fields=['full_name', 'email_id'])[0]
    finance_head_email = finance_head_user.get("email_id")
    finance_head =  finance_head_user.get("full_name")
    
    accounts_user = frappe.get_all('Management Team', filters={'designation': 'Accounts'}, fields=['full_name', 'email_id'])[0]
    accounts_team_email = accounts_user.get("email_id")
    accounts_team = accounts_user.get("full_name")

    
    