__version__ = '0.0.1'

import sys
import types

# --- HOTFIX FOR MISSING APPS ON UAT ---
# Inject a custom importer to dynamically mock out any missing old apps or their submodules.
# This prevents `bench migrate` from crashing on ModuleNotFoundError for cached hooks.
# The patch `remove_missing_apps` will then permanently clean them from the database.
class DummyMissingAppImporter:
    def find_module(self, fullname, path=None):
        if fullname.startswith("approval_app") or fullname.startswith("remittance_app"):
            return self
        return None
        
    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
            
        class DummyModule(types.ModuleType):
            def __getattr__(self, name):
                # Return a dummy function for any attribute accessed (like a Frappe hook)
                return lambda *args, **kwargs: None
                
        mod = DummyModule(fullname)
        mod.__path__ = []
        mod.__file__ = "/tmp/fake_app_for_migration/__init__.py"
        sys.modules[fullname] = mod
        return mod

if not any(isinstance(i, DummyMissingAppImporter) for i in sys.meta_path):
    sys.meta_path.insert(0, DummyMissingAppImporter())
# --------------------------------------
