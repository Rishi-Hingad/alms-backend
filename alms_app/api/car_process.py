import frappe
from alms_app.api.emailClass import EmailServices


emailer = EmailServices()
def email_formate_for_car_onbord(form_link,user_doc,company,form_name):
    body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                h1 {{
                    color: #4CAF50;
                }}
                p {{
                    font-size: 16px;
                }}
                .button {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .company-name {{
                    color: blue;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .contact-info {{
                    font-size: 14px;
                    color: grey;
                    margin-top: 20px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    padding: 8px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h1>Hello, <span class="company-name">{company}</span></h1>
            <p>Your quotation request for <strong>{user_doc.employee_name}</strong> is in progress.</p>
            <p>Please fill out the required form by clicking the link below. Ensure you carefully enter the <strong>{form_name}</strong> details and upload the necessary documents.</p>
            <p><strong>This form is for you. Please complete it carefully.</strong></p>
            <h3>Quotation Details:</h3>
            <table>
                <thead>
                    <tr>
                        <th></th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Form</td>
                        <td>{form_name}</td>
                    </tr>
                    <tr>
                        <td>User Name</td>
                        <td>{user_doc.employee_name}</td>
                    </tr>
                </tbody>
            </table>
        
            <p>
                <a href="{form_link}" class="button">Fill Car Onbord Form</a>
            </p>
            <p>Thank you for cooperating with us.</p>
            <p class="contact-info">
                For assistance, please contact:<br>
                Email: support@meril.com<br>
                Phone: +91 123 456 7890
            </p>

            <p>Thank you for your time and cooperation!</p>
        </body>
        </html>
        """
    subject =  f"Car Onbord Process for {user_doc.employee_name}"
    companies = {
                "Easy Assets":"jaykumar.patel@merillife.com",
                "ALD":"jaykumar.patel@merillife.com",
                "XYZ":"jaykumar.patel@merillife.com"
                }
    recipient_email = companies.get(company)
    emailer.send(body=body,recipient_email=recipient_email,subject=subject)



@frappe.whitelist(allow_guest=True)
def car_form_fill():
    try:
        # Extract request data
        user = frappe.form_dict.get("user")
        company = frappe.form_dict.get("company")
        quotation_id = frappe.form_dict.get("quotation_id")
        form_name = frappe.form_dict.get("form_name")
        form_status = frappe.form_dict.get("form_status")
        form_document = frappe.form_dict.get("form_document")
        
        user_doc = frappe.get_doc("Employee Master",user)  
        
        existing_doc = frappe.get_all(
                        "Car Process",
                        filters={"user": user, "company": company, "quotation": quotation_id},
                        fields=["name"]
                        )
        if existing_doc:
                doc = frappe.get_doc("Car Process", existing_doc[0].name)
                if form_name == "Purchase Form":
                    doc.purchase_document = form_document
                    doc.purchase_status = form_status 
                    form_link = form_link = f"http://127.0.0.1:8003/car-proforma-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_onbord(form_link,user_doc,company,"Proforma Invoice")           
                if form_name == "Proforma Form":
                    doc.proforma_document = form_document
                    doc.proforma_status = form_status
                    form_link = form_link = f"http://127.0.0.1:8003/car-insurance-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_onbord(form_link,user_doc,company,"Insurance Form")
                    
                if form_name == "Insurance Form":
                    print("form_document",form_document)
                    print("form_status",form_status)
                    doc.insurance_document = form_document
                    doc.insurance_status = form_status
                    # form_link = form_link = f"http://127.0.0.1:8003/car-payment-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    # email_formate_for_car_onbord(form_link,user_doc,company,"Payment Form")
                    
                    
                if form_name == "Payment Form":
                    doc.payment_document = form_document
                    doc.payment_status = form_status
                    form_link = form_link = f"http://127.0.0.1:8003/car-rto-form/new?quotation_form={quotation_id}&user={user}&company={company}"
                    email_formate_for_car_onbord(form_link,user_doc,company,"RTO Form")
                    
                if form_name == "RTO Form":
                    doc.rto_document = form_document
                    doc.rto_status = form_status
                doc.save(ignore_permissions=True)
                # frappe.msgprint("Updated existing Car Process document.")
        else:
            payload = { 
                "doctype": "Car Process",
                "user": user,
                "company": company,
                "quotation": quotation_id,
                }
            if form_name == "Purchase Form": 
                payload["purchase_status"] = form_status
                payload["purchase_document"] = form_document
            if form_name == "Payment Form":
                payload["payment_status"] = form_status
                payload["payment_document"] = form_document
            if form_name == "Insurance Form":
                payload["insurance_status"] = form_status
                payload["insurance_document"] = form_document
            if form_name == "RTO Form":
                payload["rto_status"] = form_status
                payload["rto_document"] = form_document
            if form_name == "Proforma Form":
                payload["proforma_status"] = form_status
                payload["proforma_document"] = form_document
            doc = frappe.get_doc(payload)
            doc.insert(ignore_permissions=True)
            # frappe.msgprint("Created new Car Process document.")

        # Next Email Send
        if form_name == "Purchase Form":
            pass
        elif form_name == "Payment Form":
            pass
        elif form_name == "Insurance Form":
            pass
        elif form_name == "RTO Form":
            pass
        elif form_name == "Proforma Form":
            pass
        else:
            frappe.msgprint("Something Wrong Happend!!")
    except Exception as e:
        frappe.log_error(f"Error in car_form_fill: {str(e)}", "Car Form API")
        return {"status": "error", "message": str(e)}
