import frappe

def run():
    doc = frappe.get_doc('Email Queue', 'd2t0k67fan')
    if '\r\n' not in doc.message:
        doc.message = doc.message.replace('\n', '\r\n')
        frappe.db.set_value('Email Queue', doc.name, 'message', doc.message)
        frappe.db.commit()
        print('Fixed message line endings for ' + doc.name)
    else:
        print('Message already has CRLF')
