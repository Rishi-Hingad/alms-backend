import frappe


class EmailMaster:
    """Optimized Email Service with Request-Level Caching"""

    def __init__(self):
        # Cache per request (lives only during execution)
        self._cache = {}

    # ---------------- Core Fetch ---------------- #

    def _get_users(self, designation):
        """Fetch users for a designation with caching"""
        if designation in self._cache:
            return self._cache[designation]

        users = frappe.get_all(
            "Management Team",
            filters={"designation": designation},
            fields=["full_name", "email_id"]
        )

        self._cache[designation] = users
        return users

    def _get_users_multi(self, designations):
        """Fetch users for multiple designations"""
        key = tuple(sorted(designations))

        if key in self._cache:
            return self._cache[key]

        users = frappe.get_all(
            "Management Team",
            filters={"designation": ["in", designations]},
            fields=["full_name", "email_id"]
        )

        self._cache[key] = users
        return users

    # ---------------- Helpers ---------------- #

    def _emails(self, users):
        return [u.get("email_id") for u in users if u.get("email_id")]

    def _names(self, users):
        return [u.get("full_name") for u in users if u.get("full_name")]

    def _single(self, designation):
        users = self._get_users(designation)
        return users[0] if users else {}

    # ---------------- HR ---------------- #

    @property
    def hr_team_emails(self):
        return self._emails(self._get_users("HR"))

    @property
    def hr_teams(self):
        return self._names(self._get_users("HR"))

    @property
    def hr_head_email(self):
        return self._single("HR Head").get("email_id")

    @property
    def hr_head(self):
        return self._single("HR Head").get("full_name")

    # ---------------- Travel Desk ---------------- #

    @property
    def travel_desk_email(self):
        return self._single("Travel Desk").get("email_id")

    @property
    def travel_desk_team(self):
        return self._single("Travel Desk").get("full_name")

    # ---------------- Purchase ---------------- #

    @property
    def purchase_team_email(self):
        return self._single("Purchase").get("email_id")

    @property
    def purchase_team(self):
        return self._single("Purchase").get("full_name")

    @property
    def purchase_head_email(self):
        return self._single("Purchase Head").get("email_id")

    @property
    def purchase_head(self):
        return self._single("Purchase Head").get("full_name")

    # ---------------- Finance ---------------- #

    @property
    def finance_team_emails(self):
        return self._emails(self._get_users_multi(["Finance", "Finance2"]))

    @property
    def finance_team_names(self):
        return self._names(self._get_users_multi(["Finance", "Finance2"]))

    @property
    def finance_head_emails(self):
        return self._emails(self._get_users("Finance Head"))

    @property
    def finance_head_names(self):
        return self._names(self._get_users("Finance Head"))

    # ---------------- Accounts ---------------- #

    @property
    def accounts_team_email(self):
        return self._single("Accounts").get("email_id")

    @property
    def accounts_team(self):
        return self._single("Accounts").get("full_name")

# import frappe
# import frappe.client

# class EmailMaster:
#     hr_users = frappe.get_all('Management Team', filters={'designation': 'HR'}, fields=['full_name', 'email_id'])
#     hr_team_emails = [user.email_id for user in hr_users if user.email_id]
#     hr_teams = [user.full_name for user in hr_users if user.full_name]

#     travel_desk = frappe.get_all('Management Team', filters={'designation': 'Travel Desk'}, fields=['full_name', 'email_id'])[0]
#     travel_desk_email = travel_desk.get("email_id")
#     travel_desk_team = travel_desk.get("full_name")

#     hr_head_user = frappe.get_all('Management Team', filters={'designation': 'HR Head'}, fields=['full_name', 'email_id'])[0]
#     # hr_head_email = hr_user.get("email_id")
#     hr_head_email = hr_head_user.get("email_id")
#     hr_head = hr_head_user.get("full_name")
    
#     purchase_user = frappe.get_all('Management Team', filters={'designation': 'Purchase'}, fields=['full_name', 'email_id'])[0]
#     purchase_team_email = purchase_user.get("email_id")
#     purchase_team = purchase_user.get("full_name")
    
#     purchase_head_user = frappe.get_all('Management Team', filters={'designation': 'Purchase Head'}, fields=['full_name', 'email_id'])[0]
#     purchase_head_email = purchase_head_user.get("email_id")
#     purchase_head = purchase_head_user.get("full_name")

#     finance_users = frappe.get_all('Management Team', filters={'designation': 'Finance'}, fields=['full_name', 'email_id'])
#     finance_team_emails = [user.email_id for user in finance_users if user.email_id]
#     finance_team_names = [user.full_name for user in finance_users if user.full_name]

#     finance_head_users = frappe.get_all('Management Team', filters={'designation': 'Finance Head'}, fields=['full_name', 'email_id'])
#     finance_head_emails = [user.email_id for user in finance_head_users if user.email_id]
#     finance_head_names = [user.full_name for user in finance_head_users if user.full_name]

    
#     # finance_user = frappe.get_all('Management Team', filters={'designation': 'Finance'}, fields=['full_name', 'email_id'])[0]
#     # finance_team_email = finance_user.get("email_id")
#     # finance_team = finance_user.get("full_name")
    
#     # finance_head_user = frappe.get_all('Management Team', filters={'designation': 'Finance Head'}, fields=['full_name', 'email_id'])[0]
#     # finance_head_email = finance_head_user.get("email_id")
#     # finance_head =  finance_head_user.get("full_name")

#     # finance_head2_user = frappe.get_all('Management Team', filters={'designation': 'Finance Head2'}, fields=['full_name', 'email_id'])[0]
#     # finance_head2_email = finance_head2_user.get("email_id")
#     # finance_head2 =  finance_head2_user.get("full_name")
    
#     accounts_user = frappe.get_all('Management Team', filters={'designation': 'Accounts'}, fields=['full_name', 'email_id'])[0]
#     accounts_team_email = accounts_user.get("email_id")
#     accounts_team = accounts_user.get("full_name")

    