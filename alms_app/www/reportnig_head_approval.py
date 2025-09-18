import frappe
from frappe.utils import now, get_datetime

@frappe.whitelist(allow_guest=True)
def get_car_indent_data(indent_form_id):
    """
    API endpoint to get fresh car indent form data without caching
    """
    try:
        # Validate input
        if not indent_form_id:
            return {
                "success": False,
                "message": "Missing Car Indent Form ID"
            }
        
        # Disable caching for this request
        frappe.local.flags.ignore_cache = True
        
        try:
            form_data = frappe.get_doc("Car Indent Form", indent_form_id)
        except frappe.DoesNotExistError:
            try:
                # Try to find by employee name
                employee_name = indent_form_id
                emp = frappe.get_doc("Employee Master", employee_name)
                forms = frappe.get_all(
                    "Car Indent Form",
                    filters={"employee_code": emp.name},
                    fields=["name"],
                    order_by="creation desc",
                    limit=1
                )
                if not forms:
                    return {
                        "success": False,
                        "message": f"No Car Indent Form found for {emp.employee_name}"
                    }
                form_data = frappe.get_doc("Car Indent Form", forms[0].name)
            except frappe.DoesNotExistError:
                return {
                    "success": False,
                    "message": f"No Employee Master or Car Indent Form found with ID: {indent_form_id}"
                }
        
        try:
            user = frappe.get_doc("Employee Master", form_data.employee_code)
        except frappe.DoesNotExistError:
            return {
                "success": False,
                "message": f"Employee Master not found for employee code: {form_data.employee_code}"
            }
        
        # Check approval status
        approval_status = getattr(form_data, 'approval_status', 'Pending')
        is_approved = approval_status in ['Approved', 'Rejected']
        
        # Prepare response data
        current_time = now()
        page_id = f"{form_data.name}_{get_datetime().strftime('%Y%m%d_%H%M%S_%f')}"
        
        data = {
            "success": True,
            "data": {
                "id": form_data.name,
                "page_id": page_id,
                "timestamp": current_time,
                "employee_name": user.employee_name,
                "employee_email": form_data.email_id,
                "reporting_head_name": form_data.employee_reporting,
                "vehicle_make_model": f"{form_data.make}-{form_data.model}",
                "net_ex_showroom_price": str(form_data.net_ex_showroom_price),
                "finance_amount": str(form_data.finance_amount),
                "company_name": user.company,
                "designation": user.designation,
                "eligibility": str(user.eligibility),
                "approval_status": approval_status,
                "is_approved": is_approved,
                "approval_remarks": getattr(form_data, 'approval_remarks', ''),
                "approved_by": getattr(form_data, 'approved_by', ''),
                "approval_date": str(getattr(form_data, 'approval_date', '')) if getattr(form_data, 'approval_date', '') else ''
            }
        }
        
        # Set response headers to prevent caching
        frappe.local.response.headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate, private',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Content-Type': 'application/json'
        }
        
        return data
        
    except Exception as e:
        frappe.log_error(f"Error in get_car_indent_data: {str(e)}", "Car Indent Data API Error")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }
    
import frappe
from frappe.utils import now, get_datetime
from frappe import _

def get_context(context):
    """
    Minimal context - just provide the ID, let JavaScript handle the site URL
    """
    try:
        # Get the 'id' parameter from the URL query string
        record_id = frappe.form_dict.get("id")
        
        # Provide default values to prevent template errors
        context.id = record_id or "NO_ID_PROVIDED"
        
        # Optional: Add other useful context data
        context.is_logged_in = frappe.session.user != "Guest"
        context.current_user = frappe.session.user
        
        # If no ID provided, we'll still render the page but show an error
        if not record_id:
            frappe.msgprint("❌ ID parameter is missing in the URL. Please provide a valid Car Indent Form ID.")
        
        # Prevent caching
        frappe.local.flags.ignore_cache = True
        
        return context
        
    except Exception as e:
        frappe.log_error(f"Error in get_context: {str(e)}", "Reporting Head Approval Context Error")
        # Don't throw error, just provide minimal context
        context.id = "ERROR"
        context.error_message = str(e)
        return context


# Alternative function if you want to validate the ID exists before rendering
def validate_and_get_context(context):
    """
    Enhanced version that validates the ID exists before rendering the page
    """
    try:
        record_id = frappe.form_dict.get("id")
        
        if not record_id:
            frappe.throw("❌ ID parameter is missing in the URL")
        
        # Validate that the Car Indent Form exists
        try:
            form_data = frappe.get_doc("Car Indent Form", record_id)
            context.form_exists = True
            context.employee_name = form_data.get('employee_name', 'Unknown')
        except frappe.DoesNotExistError:
            # Try to find by employee name as fallback
            try:
                emp = frappe.get_doc("Employee Master", record_id)
                forms = frappe.get_all(
                    "Car Indent Form",
                    filters={"employee_code": emp.name},
                    fields=["name"],
                    order_by="creation desc",
                    limit=1
                )
                if forms:
                    record_id = forms[0].name
                    context.form_exists = True
                    context.employee_name = emp.get('employee_name', 'Unknown')
                else:
                    frappe.throw(f"No Car Indent Form found for employee: {record_id}")
            except frappe.DoesNotExistError:
                frappe.throw(f"No Car Indent Form or Employee found with ID: {record_id}")
        
        context.id = record_id
        context.api_url = frappe.utils.get_url()
        
        # Prevent caching
        frappe.local.flags.ignore_cache = True
        
        return context
        
    except Exception as e:
        frappe.log_error(f"Error in validate_and_get_context: {str(e)}", "Reporting Head Approval Context Error")
        frappe.throw(f"An error occurred: {str(e)}")