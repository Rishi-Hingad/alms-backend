import frappe
import json
import traceback

@frappe.whitelist(allow_guest=True)
def update_payment_status():

    log = frappe.new_doc("API Log")
    log.api_url = "/api/method/crms.api.update_payment_status"
    log.api_method = "POST"

    try:
        data = frappe.local.form_dict

        # ---- STORE REQUEST BODY ---- #
        log.api_json_body = json.dumps(data)

        doctype_name = data.get("doctype_name")
        payment_status = data.get("payment_status")

        # ---- VALIDATION ---- #
        if not doctype_name or not payment_status:
            raise Exception("doctype_name and payment_status are required")

        if not frappe.db.exists("Invoice Batch", doctype_name):
            raise Exception(f"Invoice Batch {doctype_name} not found")

        doc = frappe.get_doc("Invoice Batch", doctype_name)

        # ---- UPDATE FIELD ---- #
        doc.db_set("payment_status", payment_status)

        # ---- CASCADE UPDATE (ADD HERE) ---- #
        cascade_logs, has_error = cascade_payment_update(doc, payment_status)

        # ---- SUCCESS RESPONSE ---- #
        response = {
            "message": "Payment status updated successfully" if not has_error else "Payment status updated with some failures",
            "docname": doc.name,
            "payment_status": payment_status,
            "cascade_log": cascade_logs
        }

        log.response_data = json.dumps(response)
        log.cascade_log = "\n".join(cascade_logs)
        log.status_code = 200 if not has_error else 207
        if has_error:
            log.status = "Failed"
        else:
            log.status = "Success"
        log.invoice_batch_doc = doctype_name

        log.insert(ignore_permissions=True)
        frappe.db.commit()

        return response

    except Exception as e:

        log.status = "Failed"
        log.error_message = str(e)
        log.traceback = traceback.format_exc()

        log.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.throw(str(e))

@frappe.whitelist(allow_guest=True)
def cascade_payment_update(batch_doc, payment_status):

    logs = []
    has_error = False

    try:
        if isinstance(batch_doc, str):
            batch_doc = frappe.get_doc("Invoice Batch", batch_doc)

        logs.append(f"Started cascade for Invoice Batch: {batch_doc.name}")

        for row in batch_doc.rows:

            try:
                logs.append(f"\nProcessing Row: {row.name}")

                # ---- 1. Update child row ---- #
                # row.db_set("payment_status", payment_status)
                row.payment_status = payment_status
                
                logs.append(f"Updated Batch Row payment_status")

                invoice_docname = row.invoice_document
                installment_no = row.get("installment_no")

                if not invoice_docname:
                    logs.append("Skipped: No invoice_document")
                    continue

                # ---- 2. Invoice Details ---- #
                if not frappe.db.exists("Invoice Details", invoice_docname):
                    logs.append(f"Skipped: Invoice Details not found: {invoice_docname}")
                    has_error = True
                    continue

                invoice_doc = frappe.get_doc("Invoice Details", invoice_docname)
                # invoice_doc.db_set("payment_status", payment_status)
                invoice_doc.payment_status = payment_status
                invoice_doc.save(ignore_permissions=True)
                logs.append(f"Updated Invoice Details: {invoice_docname}")

                employee = invoice_doc.get("employee_name")

                if not employee:
                    logs.append("Skipped: No employee found")
                    has_error = True
                    continue

                if not installment_no:
                    logs.append("Skipped: No installment_no")
                    has_error = True
                    continue

                # ---- 3. Vehicle Details ---- #
                vehicle_docs = frappe.get_all(
                    "Vehicle Details",
                    filters={"employee_code_and_name": employee},
                    pluck="name"
                )

                if not vehicle_docs:
                    logs.append(f"No Vehicle Details found for employee: {employee}")
                    has_error = True
                    continue

                for vd_name in vehicle_docs:
                    vd_doc = frappe.get_doc("Vehicle Details", vd_name)

                    updated = False

                    for inst in vd_doc.installment_payment:
                        # if inst.installment_no == installment_no:
                        if str(inst.installment_no) == str(installment_no):
                            # inst.db_set("installment_status", payment_status)
                            inst.installment_status = payment_status
                            logs.append(
                                f"Updated Installment {installment_no} in Vehicle: {vd_name}"
                            )
                            updated = True
                            break

                    if updated:
                        vd_doc.save(ignore_permissions=True)  # ✅ save only if changed
                    else:
                        logs.append(f"No matching installment {installment_no}")
                        has_error = True

            except Exception as row_error:
                logs.append(f"Row Failed: {str(row_error)}")
                has_error = True
        batch_doc.save(ignore_permissions=True)
        frappe.db.commit()
        logs.append("\nCascade Completed")

    except Exception as e:
        logs.append(f"Critical Failure: {str(e)}")
        has_error = True

    return logs, has_error