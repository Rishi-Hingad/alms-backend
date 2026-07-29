__version__ = '0.0.1'

import sys
import types

# --- HOTFIX FOR MISSING APPS ON UAT ---
# Inject dummy modules so `bench migrate` doesn't crash when `frappe.get_hooks()` tries to load them.
# The patch `remove_missing_apps` will then permanently clean them from the database.
for missing_app in ["approval_app", "remittance_app"]:
    if missing_app not in sys.modules:
        dummy = types.ModuleType(missing_app)
        dummy.__file__ = "/tmp/fake_app_for_migration/__init__.py"
        sys.modules[missing_app] = dummy
        sys.modules[f"{missing_app}.hooks"] = types.ModuleType(f"{missing_app}.hooks")
# --------------------------------------
