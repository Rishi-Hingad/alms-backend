import frappe

def get_emails_by_role(role_name):
    """
    Fetch all company emails for employees that have the specified designation
    and have the create_user checkbox checked.
    """
    # Fetch company_email from Employee doctype where designation matches the role_name
    # and the create_user checkbox is checked.
    emails = frappe.get_all(
        "Employee",
        filters={
            "designation": role_name,
            "create_user": 1
        },
        pluck="company_email"
    )
    
    # Filter out None or empty emails and return
    return [e for e in emails if e]
