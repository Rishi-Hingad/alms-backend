import frappe


class EmailMaster:
    """Optimized Email Service with Request-Level Caching"""

    def __init__(self):
        # Cache per request (lives only during execution)
        self._cache = {}

    # ---------------- Core Fetch ---------------- #

    def _get_users(self, designation):
        """Fetch users for a designation (role) with caching"""
        if designation in self._cache:
            return self._cache[designation]

        user_names = frappe.get_all("Has Role", filters={"role": designation, "parenttype": "User"}, pluck="parent")
        
        if not user_names:
            users = []
        else:
            users = frappe.get_all("User", filters={"name": ["in", user_names], "enabled": 1}, fields=["email as email_id", "full_name"])

        self._cache[designation] = users
        return users

    def _get_users_multi(self, designations):
        """Fetch users for multiple designations (roles)"""
        key = tuple(sorted(designations))

        if key in self._cache:
            return self._cache[key]

        user_names = frappe.get_all("Has Role", filters={"role": ["in", designations], "parenttype": "User"}, pluck="parent")
        
        if not user_names:
            users = []
        else:
            users = frappe.get_all("User", filters={"name": ["in", user_names], "enabled": 1}, fields=["email as email_id", "full_name"])

        self._cache[key] = users
        return users

    # ---------------- Helpers ---------------- #

    def _emails(self, users):
        return [u.get("email_id") for u in users if u.get("email_id") and str(u.get("email_id")).lower() != "administrator"]

    def _names(self, users):
        return [u.get("full_name") for u in users if u.get("full_name")]

    def _single(self, designation):
        users = self._get_users(designation)
        valid_users = [u for u in users if str(u.get("email_id")).lower() != "administrator"]
        return valid_users[0] if valid_users else (users[0] if users else {})

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
        return self._emails(self._get_users_multi(["Finance Team"]))

    @property
    def finance_team_names(self):
        return self._names(self._get_users_multi(["Finance Team"]))

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