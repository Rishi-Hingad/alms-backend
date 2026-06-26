from operator import or_
import frappe

# get the list of entries for approver based on the roles, team and user
def _get_entries_for_approver(employee, user, roles, status, doctype):
    """
    Returns ONLY those PRs (or records) the current approver (user/employee/role/team) is allowed to act on or see,
    filtering strictly by the next required approver. No global viewing for all approvers.

    For Pending status, only the *last* Approval Entry Details record per Approval Entry is considered.
    """
    employee_name = employee.name if employee else None
    employee_team = employee.team if employee and hasattr(employee, "team") else None

    filters = {}
    or_filters = []
    parent_filters = {"applied_to_doctype": doctype}
    if not status:
        filters["status"] = ["in", ["Pending", "Approved", "Rejected"]]
        if employee_name:
            or_filters.append(["next_approver", "=", employee_name])
        if employee_team:
            or_filters.append(["next_approver_team", "=", employee_team])
        if roles:
            or_filters.append(["next_approver_role", "in", roles])

    elif status == "Pending":
        parent_filters["status"] = "Pending"
        # Only consider last Approval Entry Details per Approval Entry
        parents = frappe.get_all("Approval Entry", filters=parent_filters, pluck="name")
        valid_parents = set()
        if parents:
            details = frappe.get_all(
                "Approval Entry Details", 
                filters={"parent": ["in", parents]},
                fields=["name", "parent", "idx", "next_approver", "next_approver_team", "next_approver_role", "status"]
            )
            # Collect last detail row per parent
            last_detail_by_parent = {}
            for row in details:
                if row["parent"] not in last_detail_by_parent or row["idx"] > last_detail_by_parent[row["parent"]]["idx"]:
                    last_detail_by_parent[row["parent"]] = row
            for detail in last_detail_by_parent.values():
                # if detail["status"] == "Pending":
                if (employee_name and detail.get("next_approver") == employee_name) or \
                    (employee_team and detail.get("next_approver_team") == employee_team) or \
                    (roles and detail.get("next_approver_role") in roles):
                    valid_parents.add(detail["parent"])
        if valid_parents:
            return set(frappe.get_all(
                "Approval Entry",
                filters={"applied_to_doctype": doctype, "name": ["in", list(valid_parents)]},
                pluck="record"
            ))
        else:
            return set()

    elif status == "Approved":
        filters["status"] = status
        filters["approved_by"] = employee_name

    elif status == "Rejected":
        filters["status"] = status
        filters["approved_by"] = employee_name
        parent_filters["status"] = status

    entries = frappe.get_all("Approval Entry Details",filters=filters,or_filters=or_filters,pluck="parent")
    if entries:
        parent_filters["name"] = ["in", entries]
        return set(frappe.get_all("Approval Entry",filters=parent_filters,pluck="record"))
    else:
        return set()
