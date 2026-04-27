import frappe
from alms_app.api.emailClass import EmailServices
import traceback

Email = EmailServices()


@frappe.whitelist(allow_guest=True)
def process_car_indent_by_reporting(indent_form, remarks, token, action):
    try:
        if action not in ["approve", "reject"]:
            return fail("Invalid action")

        if not remarks:
            return fail("Remarks are required")

        doc_name = frappe.db.get_value("Car Indent Form", {"approval_token": token}, "name")
        if not doc_name:
            return fail("Invalid or expired token")

        i_form = frappe.get_doc("Car Indent Form", doc_name)
        user = frappe.get_doc("Employee Master", i_form.employee_code)

        previous_status = i_form.reporting_head_approval or "Pending"

        new_status = "Approved" if action == "approve" else "Rejected"

        if previous_status == new_status:
            return success(
                f"Already {new_status}",
                status="no_change",
                previous_status=previous_status,
                current_status=new_status
            )

        i_form.append("approval_logs", {
            "action": new_status,
            "remarks": remarks,
            "user": frappe.session.user,
            "timestamp": frappe.utils.now()
        })

        i_form.reporting_head_approval = new_status
        i_form.reporting_head_remarks = remarks
        i_form.approval_token = None

        i_form.save(ignore_permissions=True)
        frappe.db.commit()

        if new_status == "Approved":
            Email.for_reporting_to_hr_team(user)
        else:
            Email.for_reject_by_reporting(user)

        return success(
            f"Changed from {previous_status} → {new_status}",
            status="updated",
            previous_status=previous_status,
            current_status=new_status,
            redirect_url="/approved.html" if new_status == "Approved" else "/rejected.html"
        )

    except Exception as e:
        frappe.log_error(traceback.format_exc(), "Car Indent Approval Error")
        return fail("Something went wrong")


# Helper responses (VERY IMPORTANT)
def success(message, **kwargs):
    return {
        "success": True,
        "message": message,
        **kwargs
    }


def fail(message):
    return {
        "success": False,
        "message": message,
        "redirect_url": "/somethingwrong.html"

    }