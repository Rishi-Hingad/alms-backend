# SAP Vendor Master API

## Endpoint

```text
POST /api/method/remittance_tool.remittance_tool.api.v1.vendor.upsert_vendor
```

## Authentication

Use HTTP Basic Auth with a Frappe user's API key and API secret.

```text
Authorization: Basic base64(api_key:api_secret)
Content-Type: application/json
```

Example:

```bash
curl -X POST "https://<site-url>/api/method/remittance_tool.remittance_tool.api.v1.vendor.upsert_vendor" \
  -H "Authorization: Basic <base64_api_key_colon_api_secret>" \
  -H "Content-Type: application/json" \
  -d @vendor_payload.json
```

To generate the Basic token:

```bash
printf '%s' '<api_key>:<api_secret>' | base64
```

The API user must be enabled and should have permission to create/write **Remittance Vendor**.

## Behavior

- If `Vendor` / `vendor_code` already exists, the API updates that Remittance Vendor.
- If it does not exist, the API creates a new Remittance Vendor.
- For new vendors, `Vendor` and `Name` are mandatory.
- Unknown fields are ignored and returned in `ignored_fields`.
- `Country` must already exist in **Remittance Country**. The API accepts country document name, country name, country code, or ISO code.
- `Created On` accepts `YYYYMMDD`, `YYYY-MM-DD`, `DD-MM-YYYY`, `DD/MM/YYYY`, or `YYYY/MM/DD`.

## Single Vendor Payload

```json
{
  "data": {
    "Vendor": "1000123",
    "Name": "ABC Supplier Pvt Ltd",
    "State": "Gujarat",
    "State Code": "24",
    "GSTN No": "24ABCDE1234F1Z5",
    "PAN No": "ABCDE1234F",
    "Vendor GST Classification.": "Registered",
    "Address01": "Line 1",
    "Address02": "Line 2",
    "Address03": "Line 3",
    "Address04": "Line 4",
    "Address05": "Line 5",
    "City": "Vapi",
    "Pincode": "396195",
    "Country": "India",
    "Contact No": "9999999999",
    "Alterenate No": "8888888888",
    "Email-Id": "vendor@example.com",
    "Remark": "From SAP",
    "Created On": "20260501",
    "C.Code": "1000",
    "Count": 1,
    "Currency": "INR",
    "Account Group": "ZVEN",
    "Type of Industr": "Manufacturing",
    "Payment Term": "Z030",
    "Payment Term Desc.": "Net 30 Days",
    "Reconciliation Acco": "210000"
  }
}
```

## Bulk Payload

```json
{
  "vendors": [
    {
      "Vendor": "1000123",
      "Name": "ABC Supplier Pvt Ltd"
    },
    {
      "Vendor": "1000124",
      "Name": "XYZ Supplier Pvt Ltd"
    }
  ]
}
```

## Success Response

```json
{
  "message": {
    "status": "success",
    "count": 1,
    "results": [
      {
        "status": "created",
        "name": "1000123",
        "vendor_code": "1000123",
        "ignored_fields": []
      }
    ]
  }
}
```

For updates, `results[].status` will be `updated`.

## Field Mapping

| SAP field | Remittance Vendor fieldname |
| --- | --- |
| Vendor | vendor_code |
| Name | vendor_name |
| State | state |
| State Code | state_code |
| GSTN No | gstn_no |
| PAN No | pan |
| Vendor GST Classification. | vendor_gst_classification |
| Address01 | address01 |
| Address02 | address02 |
| Address03 | address03 |
| Address04 | address04 |
| Address05 | address05 |
| City | city_district |
| Pincode | pincode |
| Country | country |
| Contact No | contact_no |
| Alterenate No | alternate_no |
| Email-Id | email_id |
| Remark | remark |
| Created On | created_on |
| C.Code | c_code |
| Count | count |
| Currency | currency |
| Account Group | account_group |
| Type of Industr | type_of_industry |
| Payment Term | terms_of_payment |
| Payment Term Desc. | payment_term_description |
| Reconciliation Acco | reconciliation_account |
