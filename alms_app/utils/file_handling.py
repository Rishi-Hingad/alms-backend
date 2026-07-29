
import frappe
from frappe.utils.file_manager import get_file_path
from frappe import _
import mimetypes
from frappe.utils import cint
import os
from werkzeug.wrappers import Response
from urllib.parse import quote

def get_file_details(file_url, doctype, docname):
    """
    Get detailed file information from file URL
    
    Args:
        file_url (str): The file URL stored in the document
        doctype (str): DocType name where file is attached
        docname (str): Document name where file is attached
    
    Returns:
        dict: File details including URL, name, size, etc.
        None: If no file URL provided
    """
    if not file_url:
        return None
    
    try:
        file_doc = frappe.get_all(
            "File",
            filters={
                "file_url": file_url,
                "attached_to_doctype": doctype,
                "attached_to_name": docname
            },
            fields=["name", "file_name", "file_url", "file_size", "is_private", "creation"]
        )
        
        if file_doc:
            file_info = file_doc[0]
            return {
                "file_url": file_info.get("file_url"),
                "file_name": file_info.get("file_name"),
                "file_size": file_info.get("file_size"),
                "is_private": file_info.get("is_private"),
                "uploaded_on": file_info.get("creation"),
                "full_url": frappe.utils.get_url() + file_info.get("file_url") if file_info.get("file_url") else None
            }
        else:
            # If file document not found, provide basic info
            return {
                "file_url": file_url,
                "full_url": frappe.utils.get_url() + file_url if file_url else None
            }
    except Exception as e:
        frappe.log_error(f"Error fetching file details: {str(e)}", "File Details Fetch Error")
        return {
            "file_url": file_url,
            "full_url": frappe.utils.get_url() + file_url if file_url else None
        }


def process_attach_fields(doc_dict, doctype, docname):
    """
    Process all attachment fields in a document dictionary and replace URLs with detailed info
    
    Args:
        doc_dict (dict): Document dictionary
        doctype (str): DocType name
        docname (str): Document name
    
    Returns:
        dict: Document dictionary with processed attachment fields
    """
    try:
        meta = frappe.get_meta(doctype)
        attach_fields = [df.fieldname for df in meta.fields if df.fieldtype in ['Attach', 'Attach Image']]
        
        for field in attach_fields:
            if doc_dict.get(field):
                doc_dict[field] = get_file_details(doc_dict[field], doctype, docname)
        
        return doc_dict
    except Exception as e:
        frappe.log_error(f"Error processing attach fields: {str(e)}", "Process Attach Fields Error")
        return doc_dict


def process_child_table_attachments(child_rows, child_doctype):
    """
    Process attachment fields in child table rows
    
    Args:
        child_rows (list): List of child table row dictionaries
        child_doctype (str): Child table DocType name
    
    Returns:
        list: Child rows with processed attachment fields
    """
    try:
        child_meta = frappe.get_meta(child_doctype)
        child_attach_fields = [df.fieldname for df in child_meta.fields if df.fieldtype in ['Attach', 'Attach Image']]
        
        processed_rows = []
        for row in child_rows:
            row_dict = row.as_dict() if hasattr(row, 'as_dict') else row
            
            for field in child_attach_fields:
                if row_dict.get(field):
                    row_dict[field] = get_file_details(
                        row_dict[field], 
                        child_doctype, 
                        row_dict.get('name')
                    )
            
            processed_rows.append(row_dict)
        
        return processed_rows
    except Exception as e:
        frappe.log_error(f"Error processing child table attachments: {str(e)}", "Child Table Attachment Error")
        return [row.as_dict() if hasattr(row, 'as_dict') else row for row in child_rows]


def save_uploaded_file(file_obj, fieldname, doctype, docname, is_private=1):
    """
    Save an uploaded file and return file information
    
    Args:
        file_obj: File object from frappe.request.files
        fieldname (str): Field name where file is attached
        doctype (str): DocType name
        docname (str): Document name
        is_private (int): 1 for private, 0 for public
    
    Returns:
        dict: File information including URL and name
        None: If file save fails
    """
    if not file_obj or not file_obj.filename:
        return None
    
    try:
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_obj.filename,
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "attached_to_field": fieldname,
            "content": file_obj.read(),
            "is_private": is_private
        })
        file_doc.save(ignore_permissions=True)
        
        return {
            "fieldname": fieldname,
            "file_url": file_doc.file_url,
            "file_name": file_doc.file_name,
            "full_url": frappe.utils.get_url() + file_doc.file_url
        }
    except Exception as e:
        frappe.log_error(
            f"Error saving file {file_obj.filename}: {str(e)}",
            "File Upload Error"
        )
        return None


def handle_file_uploads(doc, doctype):
    """
    Handle file uploads from frappe.request.files and attach them to document
    
    Args:
        doc: Frappe document object
        doctype (str): DocType name
    
    Returns:
        list: List of attached file information
    """
    attached_files = []
    
    if not frappe.request or not frappe.request.files:
        return attached_files
    
    for fieldname, file_obj in frappe.request.files.items():
        if file_obj and file_obj.filename:
            file_info = save_uploaded_file(file_obj, fieldname, doctype, doc.name)
            
            if file_info:
                # Update the document field with file URL
                setattr(doc, fieldname, file_info['file_url'])
                attached_files.append(file_info)
    
    return attached_files


def get_attach_field_names(doctype):
    """
    Get list of attachment field names for a DocType
    
    Args:
        doctype (str): DocType name
    
    Returns:
        list: List of attachment field names
    """
    try:
        meta = frappe.get_meta(doctype)
        return [df.fieldname for df in meta.fields if df.fieldtype in ['Attach', 'Attach Image']]
    except Exception as e:
        frappe.log_error(f"Error getting attach fields: {str(e)}", "Get Attach Fields Error")
        return []
    

@frappe.whitelist(allow_guest=False)
def check_user(file_id, user=None):
    if not user:
        user = frappe.session.user

    if user == "Guest":
        frappe.throw(_("You are not allowed to access this file."))

    user_exists = frappe.db.exists("User", {"name": user})
    if not user_exists:
        frappe.throw(_("Invalid user. Access denied."))

    file_doc = frappe.get_doc("File", file_id)
    if not file_doc:
        frappe.throw(_("File not found."))

    # frappe.local.response["type"] = "redirect"
    # frappe.local.response["location"] = file_doc.file_url
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = (
        f"/api/method/vms.utils.file_handling.secure_file?file_id={file_id}"
    )



@frappe.whitelist(allow_guest=False)
def secure_file(file_id=None):
    if not file_id:
        frappe.throw(_("No file ID provided"))

    if frappe.session.user == "Guest":
        frappe.throw(_("You are not authorized to access this file"))

    file_doc = frappe.get_doc("File", file_id)
    file_path = file_doc.get_full_path()

    if not os.path.exists(file_path):
        frappe.throw(_("File not found"))

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    mime_type, _ = mimetypes.guess_type(file_doc.file_name)
    mime_type = mime_type or "application/octet-stream"

    filename = file_doc.file_name
    quoted_filename = quote(filename)

    return Response(
        file_bytes,
        mimetype=mime_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quoted_filename}",
            "Cache-Control": "no-store",
        }
    )