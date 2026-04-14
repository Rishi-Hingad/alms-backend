import frappe
import shutil

def get_context(context):
    return context

@frappe.whitelist(allow_guest=True)
def get_vendor_quotation(employee_details):
    
    fields_to_fetch = [
        "revised_financed_amount",
        "location",
        "total_kilometers",
        "make",
        "revised_accessories",
        "revised_discount",
        "revised_registration_charges",
        "revised_ex_show_room_price",
        "revised_net_ex_showroom_price",
        "revised_quotation_attachment_need_to_be_done",
        "tenure_in_years"
    ]

    doc = frappe.get_all(
        "Purchase Team Form",
        filters={"name": employee_details},
        fields=fields_to_fetch,
        limit_page_length=1
    )

    if not doc:
        return None

    record = doc[0]
    print(record)

    mapped = {
        "financed_amount": record.get("revised_financed_amount") or 0,
        "location": record.get("location") or "",
        "total_kms": record.get("total_kilometers") or 0,
        "variant": record.get("make") or "",
        "accessories": record.get("revised_accessories") or 0,
        "discount_excluding_gst": record.get("revised_discount") or 0,
        "registration_charges": record.get("revised_registration_charges") or 0,
        "ex_showroom_amount": record.get("revised_ex_show_room_price") or 0,
        "ex_showroom_amount_net_of_discount": record.get("revised_net_ex_showroom_price") or 0,
        "revised_quotation_attachment_need_to_be_done": record.get("revised_quotation_attachment_need_to_be_done"),
        "tenure_in_years": record.get("tenure_in_years") or 0
    }

    file_path = record.get("revised_quotation_attachment_need_to_be_done")
    if file_path:
        file_name = file_path.split("/")[-1]
        if file_path.startswith("/private/files"):
            private_path = frappe.get_site_path("private", "files", file_name)
            public_path = frappe.get_site_path("public", "files", file_name)
            shutil.copy(private_path, public_path)
            file_path = f"/files/{file_name}"

        mapped["revised_quotation_vendor"] = file_path
        mapped["revised_quotation_vendor_name"] = file_name
        mapped["revised_quotation_vendor_url"] = frappe.utils.get_url(file_path)

    return mapped