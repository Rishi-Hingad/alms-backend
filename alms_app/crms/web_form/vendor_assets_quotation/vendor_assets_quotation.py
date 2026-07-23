import frappe
import shutil

def get_context(context):
    return context

@frappe.whitelist(allow_guest=True)
def get_vendor_quotation(employee_details=None, quotation_id=None):

    def serialize(doc):
        return {
            # identity
            "name": doc.name,
            "finance_company": doc.finance_company,
            "employee_details": doc.employee_details,
            "quote": doc.quote,

            # vehicle
            "location": doc.location,
            "total_kms": doc.total_kms,
            "variant": doc.variant,

            # pricing
            "ex_showroom_amount": doc.ex_showroom_amount,
            "ex_showroom_amount_net_of_discount": doc.ex_showroom_amount_net_of_discount,
            "accessories": doc.accessories,
            "discount_excluding_gst": doc.discount_excluding_gst,
            "registration_charges": doc.registration_charges,
            "financed_amount": doc.financed_amount,
            "base_price_excluding_gst": doc.base_price_excluding_gst,
            "gst": doc.gst,
            "base_price_less_discounts": doc.base_price_less_discounts,
            "total_discount": doc.total_discount,
            "24x7_assist": doc.get("24x7_assist"),

            # financial config
            "interest_rate": doc.interest_rate,
            "tenure": doc.tenure,
            "residual_value_percent": doc.residual_value_percent,
            "residual_value": doc.residual_value,

            # EMI engine output
            "emi_financing": doc.emi_financing,
            "finance_emi_road_tax": doc.finance_emi_road_tax,
            "gst_and_cess": doc.gst_and_cess,
            "insurance": doc.insurance,
            "fleet_management_repairs_and_tyres": doc.fleet_management_repairs_and_tyres,
            "assist_24x7": doc.get("24x7_assist"),
            "pickup_and_drop": doc.pickup_and_drop,
            "std_relief_car_non_accdt": doc.std_relief_car_non_accdt,
            "gst_on_fms": doc.gst_on_fms,

            # totals
            "total_emi": doc.total_emi,

            # attachment
            "revised_quotation_vendor": doc.revised_quotation_vendor
        }

    # CASE 1: revised flow → Car Quotation is source
    if quotation_id:
        doc = frappe.get_doc("Car Quotation", quotation_id)
        return serialize(doc)

    # CASE 2: normal flow → Purchase Form fallback
    if employee_details:
        doc = frappe.get_all(
            "Purchase Form",
            filters={"name": employee_details},
            fields=[
                "revised_financed_amount",
                "location",
                "total_kilometers",
                "make",
                "revised_accessories",
                "revised_discount",
                "revised_registration_charges",
                "revised_ex_show_room_price",
                "revised_net_ex_showroom_price",
                "tenure_in_years",
                "revised_quotation_attachment_need_to_be_done"
            ],
            limit_page_length=1
        )

        if not doc:
            return None

        r = doc[0]

        return {
            "financed_amount": r.revised_financed_amount,
            "location": r.location,
            "total_kms": r.total_kilometers,
            "variant": r.make,
            "accessories": r.revised_accessories,
            "discount_excluding_gst": r.revised_discount,
            "registration_charges": r.revised_registration_charges,
            "ex_showroom_amount": r.revised_ex_show_room_price,
            "ex_showroom_amount_net_of_discount": r.revised_net_ex_showroom_price,
            "tenure": r.tenure_in_years,
            "revised_quotation_vendor": r.revised_quotation_attachment_need_to_be_done
        }