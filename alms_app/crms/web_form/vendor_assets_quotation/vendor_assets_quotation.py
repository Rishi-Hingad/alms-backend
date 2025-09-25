# import frappe

# def get_context(context):
#     return context


# @frappe.whitelist(allow_guest=True)
# def get_vendor_quotation(employee_details):
#     """
#     Fetch Purchase Team Form.quotation_document
#     and update Car Quotation.revised_quotation_vendor
#     """
#     file_url = frappe.db.get_value(
# 		"Purchase Team Form",
# 		employee_details,   # docname
# 		"revised_quotation_attachment_need_to_be_done"
# 	)


#     if not file_url:
#         return None

#     # --- Update Car Quotation also ---
#     car_quotation_name = frappe.db.get_value(
#         "Car Quotation",
#         {"employee_details": employee_details},
#         "name"
#     )
#     if car_quotation_name:
#         frappe.db.set_value(
#             "Car Quotation",
#             car_quotation_name,
#             "revised_quotation_vendor",
#             file_url
#         )
#         frappe.db.commit()

#     return frappe.utils.get_url(file_url)



import frappe

def get_context(context):
    return context

@frappe.whitelist(allow_guest=True)
def get_vendor_quotation(employee_details):
    """
    Fetch all relevant fields from Purchase Team Form for a given employee_details.
    Also returns quotation document URL for revised_quotation_vendor.
    """
    fields_to_fetch = [
        "revised_financed_amount",
        "location",
        "kilometers_per_year",
        "make",
        "revised_accessories",
        "revised_discount",
        "revised_registration_charges",
        "revised_ex_show_room_price",
        "revised_net_ex_showroom_price",
        "revised_quotation_attachment_need_to_be_done"
    ]

    # Fetch the document using employee_details as docname
    doc = frappe.get_all(
        "Purchase Team Form",
        filters={"name": employee_details},
        fields=fields_to_fetch,
        limit_page_length=1
    )

    if not doc:
        return None

    record = doc[0]

    # Build a mapping to Car Quotation fieldnames
    mapped = {
        "financed_amount": record.get("revised_financed_amount", "0"),
        "location": record.get("location", ""),
        "kms": record.get("kilometers_per_year", "0"),
        "variant": record.get("make", ""),
        "accessory": record.get("revised_accessories", 0),
        "discount_excluding_gst": record.get("revised_discount", 0),
        "registration_charges": record.get("revised_registration_charges", 0),
        "ex_showroom_amount": record.get("revised_ex_show_room_price", "0"),
        "ex_showroom_amount_net_of_discount": record.get("revised_net_ex_showroom_price", 0),
        "revised_quotation_attachment_need_to_be_done": record.get("revised_quotation_attachment_need_to_be_done")
    }

    # Handle attachment
    if record.get("revised_quotation_attachment_need_to_be_done"):
        file_name = record["revised_quotation_attachment_need_to_be_done"].split("/").pop()
        file_path = f"/files/{file_name}"
        mapped["revised_quotation_vendor"] = file_path
        mapped["revised_quotation_vendor_url"] = frappe.utils.get_url(file_path)

    return mapped
