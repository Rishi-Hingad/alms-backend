



import frappe
from alms_app.api.emailClass import EmailServices


EMail = EmailServices()
@frappe.whitelist()
def email_sender(name, email_send_to=None):
    try:
        user = frappe.get_doc("Employee Master",name)
        print(f"------------[{user.email_id}]-----------------[EMAIL API WORK]--------------[{email_send_to}]---------------")
        
        if email_send_to =="To Employee":
            EMail.for_hr_team_to_employee(user)
            
        elif email_send_to == "To Reporting":
            EMail.for_employee_to_reporting(user) 
            
        elif email_send_to =="Reporting To HR":
            EMail.for_reporting_to_hr_team(user) 
        
        elif email_send_to =="HR To HRHead":
            EMail.for_hr_team_to_hr_head(user) 
        
        elif email_send_to =="HRHead To PurchaseTeam":
            EMail.for_hr_head_to_purchase_team(user) 
            
        elif email_send_to =="PurchaseTeam To PurchaseHead":
            EMail.for_purchase_team_to_purchase_head(user) 
            
        elif email_send_to =="PurchaseHead To FinanceTeam":
            EMail.for_purchase_head_to_finance_team(user) 
        
        elif email_send_to =="FinanceTeam To FinanceHead":
            EMail.for_finance_team_to_finance_head(user) 
            
        elif email_send_to =="FinanceHead To AccountsTeam":
            EMail.for_finance_head_to_accounts_team(user)
        return {"status": "success", "message": f"Email sent"}
    except Exception as e:
        print(f"------------[Error:{e}]---------------")
        return {"status": "error","message":str(e)}
