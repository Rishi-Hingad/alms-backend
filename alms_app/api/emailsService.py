from pydoc import doc
import frappe
from alms_app.api.emailClass import EmailServices
import json
import traceback
from frappe import _

Email = EmailServices()

@frappe.whitelist(allow_guest=True)
def email_sender(name, email_send_to=None, car_indent_form_name=None, payload=None):
    try:
        if payload and isinstance(payload, str):
            payload = json.loads(payload)

        user = frappe.get_doc("Employee",name)
        print("------------[email sender name]------------------:",user)
        print("------------[email send to]------------------:",email_send_to)
        print("------------[payload]------------------:", payload)
        
        if email_send_to =="To Employee":
            Email.for_hr_team_to_employee(user)
            
        elif email_send_to == "To Reporting":
            Email.for_employee_to_reporting(user.name, car_indent_form_name)

        elif email_send_to == "To HR (New Request)":
            Email.for_employee_to_hr_team(user.name, car_indent_form_name)

        elif email_send_to =="ReportingHead To HR":
            Email.for_reporting_to_hr_team(user) #changed here
                   
        elif email_send_to =="HR To Travel Desk":
            Email.for_hr_team_to_travel_desk(user)
        
        elif email_send_to =="Travel Desk To HRHead":
            Email.for_travel_desk_to_hr_head(user)            
            # Email.acknowledgement_email(user,"Travel Desk Department","HR Head")

        # elif email_send_to =="HR To HRHead":
        #     Email.for_hr_team_to_hrhead(user)
        
        elif email_send_to =="HRHead To PurchaseForm":
            Email.for_hr_head_to_purchase_team(user) 
            Email.acknowledgement_email(user,"HR Department","Purchase Department")
            
        elif email_send_to =="PurchaseForm To PurchaseHead":
            Email.for_purchase_team_to_purchase_head(user) 
            
        elif email_send_to =="PurchaseHead To FinanceTeam":
            Email.for_purchase_head_to_finance_team(user) 
            Email.acknowledgement_email(user,"Purchase Department","Finance Department")

        elif email_send_to == "Reject PurchaseHead to PurchaseForm":
            Email.for_reject_by_purchase_head(user)

        # From Purchase Form to Vendor (By Finance Team)  
        elif email_send_to == "FinanceHead To Quotation Company":
            return Email.for_car_quotation(user,payload)
            
        elif email_send_to =="FinanceTeam To FinanceHead":
            Email.for_finance_team_to_finance_head(user) 
        
        elif email_send_to =="FinanceTeam To FinanceHead Payload":
            Email.for_finance_team_to_finance_head_payload(user,payload) 
            
        elif email_send_to == "FinanceHead To All":

            quotation_id = payload.get("quotation_id") if payload else None

            if quotation_id:
                # Send to selected company process
                Email.for_selected_compny_process(quotation_id=quotation_id)
            
            # Email.for_finance_head_to_accounts_team(user)
            # Email.for_finance_head_to_finance_team(user, quotation_id)
            Email.acknowledgement_email(user,"Finance Department","Final Approval")  #change to congratualate mail,  finance head to employee
            
        # From Vendor to Finance Team (By Vendor)
        elif email_send_to == "Finance Fill Quotation Acknowledgement":
            return Email.for_finance_fill_quotation_acknowledgement(user, payload)
            
            # negative track starts here
        elif email_send_to == "Deduction Finance Team To Finance Head":
            Email.for_deduction_finance_to_finance_head(user,payload)

        elif email_send_to == "Deduction Finance Head To Accounts":
            Email.for_deduction_finance_head_to_accounts(user,payload)

        elif email_send_to == "Reject Finance Head To Finance Team":
            Email.for_reject_deduction_by_finance_head(user,payload)

         #rejection
        elif email_send_to=="Reject Reporting to Employee":
            Email.for_reject_by_reporting(user)
        
        elif email_send_to=="Reject HRTeam to Employee":
            Email.for_reject_by_hr_team(user)
        
        elif email_send_to=="Reject TravelDesk to Employee":
            Email.for_reject_by_travel_desk(user)
        
        elif email_send_to=="Reject HRHead to Employee":
            Email.for_reject_by_hr_head(user)

        elif email_send_to=="Reject PurchaseHead to PurchaseForm":
            Email.for_reject_by_purchase_head(user)

        elif email_send_to=="Reject PurchaseForm to HR":
            Email.for_reject_by_purchase_team(user) 

        elif email_send_to== "Reject FinanceHead to FinanceTeam": #update the function
            if payload.get("quotation_id"):
                Email.for_reject_finance_head_to_finance_team(quotation_id=payload.get("quotation_id"))
            else:
                frappe.msgprint("Something Wrong!, Try Again!!!")

        elif email_send_to== "Reject FinanceTeam to Vendor":
            if payload.get("quotation_id"):
                Email.for_reject_finance_team_to_vendor(quotation_id=payload.get("quotation_id"))
            else:
                frappe.msgprint("Something Wrong!, Try Again!!")


        return {"status": "success", "message": "Email sent successfully!"}
    except Exception as e:
        frappe.log_error(f"Email Sender Error for {email_send_to}: {str(e)}\n{traceback.format_exc()}", "Email Sender Error")
        return {"status": "error","message":str(e)}

