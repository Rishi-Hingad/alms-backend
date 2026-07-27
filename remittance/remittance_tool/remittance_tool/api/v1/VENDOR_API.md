# Vendor Sync API (SAP ↔ Remittance Tool)

This API lets the SAP team push vendor lifecycle events into the Remittance
Tool so the local `Remittance Vendor` master stays in sync.

**Base path:** `/api/method/remittance_tool.remittance_tool.api.v1.vendor.<endpoint>`

**Content-Type:** `application/json`

---

## Authentication

All write endpoints require **HTTP Basic Auth**:

```
Authorization: Basic <base64(api_key:api_secret)>
```

Generate the key/secret pair from a Frappe User document
(`User > API Access > Generate Keys`). Use a dedicated service user (e.g.
`sap-sync@meril.local`) with the `System Manager` role or a custom role that
has create/write/delete on `Remittance Vendor`.

`GET upsert_vendor` is unauthenticated and returns a reachability ping.

---

## Endpoints at a glance

| Endpoint | Method | Purpose |
|---|---|---|
| `upsert_vendor` | `POST` | Create new vendor or update existing (idempotent) |
| `block_vendor` | `POST` | Mark vendor as disabled (soft block) |
| `unblock_vendor` | `POST` | Clear the disabled flag |
| `delete_vendor` | `POST` | Hard delete if unused; soft-block if referenced |
| `upsert_vendor` | `GET` | Reachability ping (no auth) |

---

## Common response envelope

Every write endpoint returns the same envelope:

```json
{
  "status": "success",            // "success" | "partial" | "failed"
  "count": 2,
  "succeeded": 2,
  "failed": 0,
  "results": [
    { "status": "success", "vendor_code": "V001", "name": "V001", "action": "created", "ignored_fields": [] },
    { "status": "success", "vendor_code": "V002", "name": "V002", "action": "updated", "ignored_fields": [] }
  ]
}
```

- Each row in `results` is committed independently — a single bad vendor in
  a batch will be marked `status: "error"` but the rest succeed.
- `action` is one of `created | updated | blocked | unblocked | deleted | soft_deleted | already_absent`.
- `ignored_fields` lists payload keys that didn't match any known vendor field
  (helpful for debugging stale SAP column names).
- HTTP status is always `200`. Inspect the `status`/`failed` fields in the body.

On a per-row error you'll see:

```json
{ "status": "error", "vendor_code": "BADCODE", "error": "Vendor BADCODE not found" }
```

---

## 1. `upsert_vendor` — create or update

`POST /api/method/remittance_tool.remittance_tool.api.v1.vendor.upsert_vendor`

Idempotent: lookup is by `vendor_code`. If found → update; otherwise → insert.
For new vendors, both `vendor_code` and `vendor_name` are required.

### Accepted payload shapes

```jsonc
// Single vendor
{ "vendor_code": "V001", "vendor_name": "ACME Pvt Ltd", "country": "India" }

// Single vendor wrapped
{ "data": { "vendor_code": "V001", "vendor_name": "ACME" } }

// Bulk
{ "vendors": [ { "vendor_code": "V001", "vendor_name": "ACME" }, { "vendor_code": "V002", "vendor_name": "Bravo" } ] }

// Bulk array
[ { "vendor_code": "V001", ... }, { "vendor_code": "V002", ... } ]
```

### Field mapping

The API accepts SAP's column names as well as our internal names. Examples
(case-insensitive, separators `_` `.` and spaces are normalized):

| SAP / payload key | Stored as |
|---|---|
| `LIFNR`, `vendor`, `vendor code`, `vendor_code` | `vendor_code` |
| `NAME1`, `name`, `vendor name`, `vendor_name` | `vendor_name` |
| `gst no`, `gstn no`, `gstn_no` | `gstn_no` |
| `pan`, `pan no` | `pan` |
| `address1` … `address5`, `address01` … `address05` | `address01` … `address05` |
| `town city district`, `city`, `city_district` | `city_district` |
| `pin code`, `pincode` | `pincode` |
| `country` (name / ISO / code) | `country` (resolved against `Remittance Country`) |
| `email-id`, `email id` | `email_id` |
| `created on` (`YYYY-MM-DD`, `DD-MM-YYYY`, `DD/MM/YYYY`, `YYYYMMDD`) | `created_on` |
| `c.code`, `c code` | `c_code` |
| `payment term`, `terms of payment` | `terms_of_payment` |
| `reconciliation acco` (truncated SAP header) | `reconciliation_account` |

Unknown keys are silently dropped and reported in `ignored_fields`. See the
full alias map in [`vendor.py`](vendor.py) (`VENDOR_FIELD_ALIASES`).

### Country resolution

`country` accepts any of:
- The Remittance Country `name` (e.g. `"India"`)
- `country_name`
- `country_code` (e.g. `"IN"`)
- `iso_code`

If none match → row fails with `Country '<value>' does not exist in Remittance Country`.

### Example — single vendor

```bash
curl -X POST https://<site>/api/method/remittance_tool.remittance_tool.api.v1.vendor.upsert_vendor \
  -u "<api_key>:<api_secret>" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_code": "V0001",
    "vendor_name": "Acme Imports LLC",
    "pan": "AAAPL1234C",
    "gstn_no": "27AAAPL1234C1Z5",
    "country": "United States",
    "city_district": "New York",
    "pincode": "10001",
    "email_id": "ap@acme.example",
    "created_on": "20260415"
  }'
```

### Example — bulk

```bash
curl -X POST https://<site>/api/method/remittance_tool.remittance_tool.api.v1.vendor.upsert_vendor \
  -u "<api_key>:<api_secret>" \
  -H "Content-Type: application/json" \
  -d '{
    "vendors": [
      { "vendor_code": "V0001", "vendor_name": "Acme" },
      { "vendor_code": "V0002", "vendor_name": "Bravo" }
    ]
  }'
```

---

## 2. `block_vendor` — soft-disable

`POST /api/method/remittance_tool.remittance_tool.api.v1.vendor.block_vendor`

Sets `disabled=1` and writes a `block_reason`. Disabled vendors are
automatically excluded from Frappe Link dropdowns (so makers can't pick a
blocked vendor in a new Form 15CB) but historical references stay intact.

### Payload shapes

```jsonc
{ "vendor_code": "V0001", "reason": "Tax non-compliance per SAP" }
{ "vendor_codes": ["V0001", "V0002"], "reason": "Bulk hold" }
[ "V0001", "V0002" ]
"V0001"
```

If `reason` is omitted, a default is recorded:
`BLOCKED via SAP API at <timestamp>`.

### Example

```bash
curl -X POST https://<site>/api/method/remittance_tool.remittance_tool.api.v1.vendor.block_vendor \
  -u "<api_key>:<api_secret>" \
  -H "Content-Type: application/json" \
  -d '{ "vendor_code": "V0001", "reason": "Compliance hold" }'
```

---

## 3. `unblock_vendor` — re-enable

`POST /api/method/remittance_tool.remittance_tool.api.v1.vendor.unblock_vendor`

Clears `disabled` and `block_reason`.

### Payload shapes

Same as `block_vendor` (no `reason`).

```bash
curl -X POST https://<site>/api/method/remittance_tool.remittance_tool.api.v1.vendor.unblock_vendor \
  -u "<api_key>:<api_secret>" \
  -H "Content-Type: application/json" \
  -d '[ "V0001", "V0002" ]'
```

---

## 4. `delete_vendor` — sync deletion

`POST /api/method/remittance_tool.remittance_tool.api.v1.vendor.delete_vendor`

Per-vendor logic:

| Condition | Action | `action` field in response |
|---|---|---|
| Vendor does not exist | no-op | `already_absent` |
| Vendor exists, no references | hard delete via `frappe.delete_doc` | `deleted` |
| Vendor exists, has references | soft-block (`disabled=1` + reason) | `soft_deleted` |
| `force: true` AND has references | hard delete (will break references) | `deleted` |

References are detected automatically by walking every `Link`/`Dynamic Link`
field in the database that points to `Remittance Vendor` (e.g. the `vendor`
link on `Remittance Form 15 CB`). New link doctypes need no code change.

### Payload shapes

```jsonc
{ "vendor_code": "V0001", "reason": "Closed in SAP" }
{ "vendor_codes": ["V0001", "V0002"], "reason": "Mass cleanup" }
{ "vendor_code": "V0001", "force": true }   // hard delete even if referenced — use carefully
```

### Example — safe delete (recommended)

```bash
curl -X POST https://<site>/api/method/remittance_tool.remittance_tool.api.v1.vendor.delete_vendor \
  -u "<api_key>:<api_secret>" \
  -H "Content-Type: application/json" \
  -d '{ "vendor_code": "V0001", "reason": "DELETED in SAP on 2026-05-02" }'
```

---

## SAP integration recipe

Recommended event-to-endpoint mapping for the SAP team:

| SAP event | Endpoint |
|---|---|
| Create new vendor (`XK01`) | `upsert_vendor` |
| Update vendor (`XK02`) | `upsert_vendor` |
| Mark for deletion / block (`XK06`, `XK05`) | `block_vendor` |
| Unblock | `unblock_vendor` |
| Archived / removed in SAP | `delete_vendor` |

Idempotency: `upsert_vendor` is idempotent on `vendor_code`, and block /
unblock / delete are also safe to retry. SAP can replay the same event
without producing duplicates.

---

## Error handling cheat sheet

| Symptom | Likely cause |
|---|---|
| HTTP 401 / `AuthenticationError` | Missing or wrong Basic Auth header |
| Per-row `Vendor code is required` | Missing `vendor_code` in payload |
| Per-row `Vendor name is required for new vendor` | New vendor without `vendor_name` |
| Per-row `Country '<x>' does not exist` | Country not present in `Remittance Country` master |
| Per-row `Vendor <x> not found` | block/unblock/delete on a non-existent vendor (delete will return `already_absent` instead) |
| `ignored_fields` populated | SAP sent extra columns; safe to ignore unless you expected them to map |

For deeper traces, check `Error Log` in Desk — every row failure logs a
full traceback under `Vendor API error (<worker>)`.

---

## Operational notes

- **Idempotency / replays**: All endpoints are idempotent. SAP can safely
  retry a failed call.
- **Per-row commits**: A bad row inside a bulk request fails alone — earlier
  successful rows in the same batch are already committed.
- **Disabled vendors stay readable**: blocking only hides the vendor from
  link-field dropdowns. Historical Form 15CB documents still resolve and
  print fine.
- **Hard delete is safe by default**: if any document still references the
  vendor, the row is auto-converted to a soft-block. Use `force: true` only
  for true cleanup of orphan records.
- **Sync direction is one-way (SAP → us)**. Changes made manually in our
  Desk UI do not flow back to SAP.

---

## Test from bench (no HTTP)

```bash
bench --site remittance execute remittance_tool.remittance_tool.api.v1.vendor.upsert_vendor \
  --kwargs '{"data": {"vendor_code": "TEST01", "vendor_name": "Test Vendor", "country": "India"}}'

bench --site remittance execute remittance_tool.remittance_tool.api.v1.vendor.block_vendor \
  --kwargs '{"vendor_code": "TEST01", "reason": "Smoke test"}'

bench --site remittance execute remittance_tool.remittance_tool.api.v1.vendor.delete_vendor \
  --kwargs '{"vendor_code": "TEST01"}'
```
