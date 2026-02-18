import frappe
import frappe.client

class EmailMaster:
    hr_users = frappe.get_all('Management Team', filters={'designation': 'HR'}, fields=['full_name', 'email_id'])
    hr_team_emails = [user.email_id for user in hr_users if user.email_id]
    hr_teams = [user.full_name for user in hr_users if user.full_name]

    travel_desk = frappe.get_all('Management Team', filters={'designation': 'Travel Desk'}, fields=['full_name', 'email_id'])[0]
    travel_desk_email = travel_desk.get("email_id")
    travel_desk_team = travel_desk.get("full_name")

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

    finance_users = frappe.get_all(
    'Management Team',
    filters={'designation': 'Finance'},
    fields=['full_name', 'email_id']
    )

    finance_team_emails = [user.email_id for user in finance_users if user.email_id]
    finance_team_names = [user.full_name for user in finance_users if user.full_name]

    finance_head_users = frappe.get_all(
        'Management Team',
        filters={'designation': 'Finance Head'},
        fields=['full_name', 'email_id']
    )

    finance_head_emails = [user.email_id for user in finance_head_users if user.email_id]
    finance_head_names = [user.full_name for user in finance_head_users if user.full_name]

    
    # finance_user = frappe.get_all('Management Team', filters={'designation': 'Finance'}, fields=['full_name', 'email_id'])[0]
    # finance_team_email = finance_user.get("email_id")
    # finance_team = finance_user.get("full_name")
    
    # finance_head_user = frappe.get_all('Management Team', filters={'designation': 'Finance Head'}, fields=['full_name', 'email_id'])[0]
    # finance_head_email = finance_head_user.get("email_id")
    # finance_head =  finance_head_user.get("full_name")

    # finance_head2_user = frappe.get_all('Management Team', filters={'designation': 'Finance Head2'}, fields=['full_name', 'email_id'])[0]
    # finance_head2_email = finance_head2_user.get("email_id")
    # finance_head2 =  finance_head2_user.get("full_name")
    
    accounts_user = frappe.get_all('Management Team', filters={'designation': 'Accounts'}, fields=['full_name', 'email_id'])[0]
    accounts_team_email = accounts_user.get("email_id")
    accounts_team = accounts_user.get("full_name")

    