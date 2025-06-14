import frappe
from alms_app.api.emailClass import EmailServices
import json

EMail = EmailServices()
@frappe.whitelist(allow_guest=True)
def email_sender(name, email_send_to=None,payload=None):
    try:
        if payload:
            payload = json.loads(payload)

        user = frappe.get_doc("Employee Master",name)
        print("------------[email sender name]------------------:",user)
        
        if email_send_to =="To Employee":
            EMail.for_hr_team_to_employee(user)
            
        elif email_send_to == "To Reporting":
            EMail.for_employee_to_reporting(user)

        elif email_send_to =="ReportingHead To HR":
            EMail.for_reporting_to_hr_team(user) #changed here
                   
        elif email_send_to =="HR To Travel Desk":
            EMail.for_hr_team_to_travel_desk(user)
        
        elif email_send_to =="Travel Desk To HRHead":
            EMail.for_travel_desk_to_hr_head(user)            
            EMail.acknowledgement_email(user,"Travel Desk Department","HR Head")
        
        elif email_send_to =="HRHead To PurchaseTeam":
            EMail.for_hr_head_to_purchase_team(user) 
            EMail.acknowledgement_email(user,"HR Department","Purchase Department")
            
        elif email_send_to =="PurchaseTeam To PurchaseHead":
            EMail.for_purchase_team_to_purchase_head(user) 
            
        elif email_send_to =="PurchaseHead To FinanceTeam":
            EMail.for_purchase_head_to_finance_team(user) 
            EMail.acknowledgement_email(user,"Purchase Department","Finance Department")
            
        elif email_send_to == "FinanceHead To Quotation Company":
            EMail.for_car_quotation_ALD_EasyAssets_Xyz(user,payload)
            
        elif email_send_to =="FinanceTeam To FinanceHead":
            EMail.for_finance_team_to_finance_head(user) 
        
        elif email_send_to =="FinanceTeam To FinanceHead Payload":
            EMail.for_finance_team_to_finance_head_payload(user,payload) 
            
        elif email_send_to =="FinanceHead To AccountsTeam":# FinanceHead To Vendors also
            # print("------------[PAYLOAD Quoatation ID]------------------:",payload)
            EMail.for_finance_head_to_accounts_team(user)
            if payload.get("quotation_id"):
                EMail.for_selected_compny_process(quotation_id=payload.get("quotation_id"))
            else:
                frappe.msgprint("Something Wrong!, Try Again")
            EMail.acknowledgement_email(user,"Finance Department","Final Approval")  #change to congratualate mail,  finance head to employee
            
        elif email_send_to in ["Easy Assets","ALD","XYZ"]:
            EMail.for_finance_fill_quotation_acknowledgement(user,email_send_to)
            # negative track starts here
        elif email_send_to == "Deduction Finance Team To Finance Head":
            EMail.for_deduction_finance_to_finance_head(user,payload)
        elif email_send_to == "Deduction Finance Head To Accounts":
            EMail.for_deduction_finance_head_to_accounts(user,payload)
        elif email_send_to == "Reject Finance Head To Finance Team":
            EMail.for_reject_deduction_by_finance_head(user,payload)
         #rejection
        elif email_send_to=="Reject Reporting to Employee":
            EMail.for_reject_by_reporting(user)
        
        elif email_send_to=="Reject HRTeam to Employee":
            EMail.for_reject_by_hr_team(user)
        
        elif email_send_to=="Reject TravelDesk to Employee":
            EMail.for_reject_by_travel_desk(user)
        
        elif email_send_to=="Reject HRHead to Employee":
            EMail.for_reject_by_hr_head(user)

        elif email_send_to=="Reject PurchaseHead to PurchaseTeam":
            EMail.for_reject_by_purchase_head(user)  

        elif email_send_to== "Reject FinanceHead to Vendor":
            if payload.get("quotation_id"):
                EMail.for_reject_finance_head_to_vendor(quotation_id=payload.get("quotation_id"))
            else:
                frappe.msgprint("Something Wrong!, Try Again!!!")

        elif email_send_to== "Reject FinanceTeam to Vendor":
            if payload.get("quotation_id"):
                EMail.for_reject_finance_team_to_vendor(quotation_id=payload.get("quotation_id"))
            else:
                frappe.msgprint("Something Wrong!, Try Again!!")


        return {"status": "success", "message": f"Email sent"}
    except Exception as e:
        # print(f"------------[Error:{e}]---------------")
        return {"status": "error","message":str(e)}

import traceback

@frappe.whitelist(allow_guest=True)
def approve_car_indent_by_reporting(indent_form, remarks):
    try: 
        user = frappe.get_doc("Employee Master", indent_form)
        i_form = frappe.get_doc("Car Indent Form", indent_form)
        
        i_form.reporting_head_approval = "Approved"
        i_form.reporting_head_remarks = remarks
        i_form.save()
        frappe.db.commit()
        
        print("approve_car_indent_by_reporting ja rha hai +++++++++++++++++++++++")
        EMail.for_reporting_to_hr_team(user) 
        
        # Redirect on success
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/approved"
    
    except Exception as e:
        error_message = str(e)
        print("Error occurred:", error_message)
        print("Exception type:", type(e))
        print("Full Traceback:\n", traceback.format_exc())
        
        # Log the error for debugging
        frappe.log_error(f"Error approving form: {error_message}", "Car Indent Approval Error")

        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/somethingwrong"
        return
