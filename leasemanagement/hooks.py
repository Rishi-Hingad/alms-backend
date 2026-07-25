# Dummy hooks file for leasemanagement to resolve ModuleNotFoundError during migration

app_name = "leasemanagement"
app_title = "Lease Management (Legacy)"
app_publisher = "Rishi Hingad"
app_description = "Legacy app name reference for migration"
app_email = "rishi.hingad@merillife.com"
app_license = "mit"

before_migrate = "leasemanagement.rename_app.execute"
