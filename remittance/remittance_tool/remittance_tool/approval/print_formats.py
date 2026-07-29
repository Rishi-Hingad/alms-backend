"""Print Format installer for Remittance Form 15 CB.

Creates / updates a single Print Format record named "Form 15CB" against the
"Remittance Form 15 CB" doctype.

Run from bench:
    bench --site <site> execute remittance_tool.remittance_tool.approval.print_formats.install
"""
import frappe


_HTML = r"""{% set company_name = frappe.db.get_value("Remittance Company", doc.company, "company_name") or doc.company or "" %}
{% set vendor_name = frappe.db.get_value("Remittance Vendor", doc.vendor, "vendor_name") or doc.vendor or "" %}
{% set vendor_addr_parts = [] %}
{% set _v = frappe.get_cached_doc("Remittance Vendor", doc.vendor) if doc.vendor else None %}
{% if _v %}
  {% if _v.address_line_1 %}{% set _ = vendor_addr_parts.append(_v.address_line_1) %}{% endif %}
  {% if _v.address_line_2 %}{% set _ = vendor_addr_parts.append(_v.address_line_2) %}{% endif %}
  {% if _v.road_street %}{% set _ = vendor_addr_parts.append(_v.road_street) %}{% endif %}
  {% if _v.area_locality %}{% set _ = vendor_addr_parts.append(_v.area_locality) %}{% endif %}
  {% if _v.city_district %}{% set _ = vendor_addr_parts.append(_v.city_district) %}{% endif %}
  {% if _v.state %}{% set _ = vendor_addr_parts.append(_v.state) %}{% endif %}
  {% if _v.country %}{% set _ = vendor_addr_parts.append(_v.country) %}{% endif %}
{% endif %}
{% set vendor_address_full = doc.vendor_address or (vendor_addr_parts | join(", ")) %}
{% set country_label = frappe.db.get_value("Remittance Country", doc.country_to_remit, "country_name") or doc.country_to_remit or "—" %}
{% set currency_label = doc.currency or "—" %}
{% set nature_label = frappe.db.get_value("Remittance Nature", doc.nature_of_remittance, "nature_of_remittance") or doc.nature_of_remittance or "—" %}
{% set bank_branch_label = frappe.db.get_value("Remittance Bank Branch", doc.bank_branch, "branch_name") or doc.bank_branch or "" %}
{% set bank_name_label = doc.bank_name or "" %}
{% set bank_full = (bank_name_label ~ (" " ~ bank_branch_label if bank_branch_label else "")).strip() or "—" %}

<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body, .print-format { font-family: Arial, sans-serif; font-size: 9pt; color: #000; background: #fff; }
  .cb-wrap { width: 100%; padding: 6mm 8mm; }

  /* Top header row: Tax Documents (left) + Doc box (right) */
  .top-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
  .tax-docs { font-size: 9pt; }
  .tax-docs h4 { font-size: 9pt; font-weight: bold; text-decoration: underline; margin-bottom: 4px; }
  .tax-docs table { border-collapse: collapse; }
  .tax-docs td { padding: 1px 12px 1px 0; }
  .doc-box { border: 1px solid #000; border-collapse: collapse; min-width: 220px; }
  .doc-box td { border: 1px solid #000; padding: 3px 8px; font-size: 9pt; }
  .doc-box td.lbl { font-weight: bold; background: #f5f5f5; width: 50%; }

  /* Title block (centered, between header and intro) */
  .title-block { text-align: center; margin: 6px 0 10px; }
  .title-block h2 { font-size: 13pt; font-weight: bold; }
  .title-block .rule { font-size: 10pt; font-style: italic; }
  .title-block .sub { font-size: 9pt; }

  /* Intro paragraph (with bold remitter/beneficiary lines) */
  .intro { text-align: center; margin: 6px 0 0; font-size: 9pt; line-height: 1.45; }
  .intro p { margin-bottom: 2px; }
  .intro .strong { font-weight: bold; }

  /* Main form table */
  .form-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  .form-table td { border: 1px solid #000; padding: 5px 7px; vertical-align: top; font-size: 9pt; }
  .col-letter { width: 22px; text-align: center; font-weight: bold; vertical-align: middle; }
  .col-num    { width: 22px; text-align: center; font-weight: bold; }
  .col-label  { width: 48%; }
  .col-value  { width: auto; }
  .form-table .split-2 { display: flex; justify-content: space-between; gap: 12px; }
  .form-table .split-2 > div { flex: 1; }
  .nested-list { width: 100%; border-collapse: collapse; }
  .nested-list td { border: none; padding: 2px 4px; vertical-align: top; }
  .nested-list td.k { width: 50%; }
  .indent-1 { padding-left: 14px !important; }
  .indent-2 { padding-left: 28px !important; }
  .yes-no { font-style: italic; }
  .center { text-align: center; }
  .small { font-size: 8pt; }
  .no-break { page-break-inside: avoid; }

  /* Signature */
  .sig-block { margin-top: 18px; display: flex; justify-content: space-between; font-size: 8.5pt; }
  .sig-left, .sig-right { width: 48%; }
  .sig-right { text-align: right; }
  .sig-line { border-top: 1px solid #000; margin-top: 28px; padding-top: 3px; }
</style>

{# Pre-extract tax document years for top-left summary #}
{% set tdoc_rows = [] %}
{% for td in (doc.tax_documents or []) %}
  {% set yr = (td.effective_from or td.effective_to) %}
  {% set yr = (yr.year if yr and yr.__class__.__name__ in ("date", "datetime") else (yr[:4] if yr else "")) %}
  {% set _ = tdoc_rows.append({"type": td.tax_document_type or "—", "year": yr or "—"}) %}
{% endfor %}

<div class="cb-wrap">

  <!-- Top-of-page header: Tax Documents (left) and Doc box (right) -->
  <div class="top-row no-break">
    <div class="tax-docs">
      <h4>Tax Documents</h4>
      <table>
        {% if tdoc_rows %}
          {% for r in tdoc_rows %}
          <tr><td>{{ r.type }}</td><td>{{ r.year }}</td></tr>
          {% endfor %}
        {% else %}
          <tr><td colspan="2" style="color:#666;">—</td></tr>
        {% endif %}
      </table>
    </div>

    <table class="doc-box">
      <tr><td class="lbl">Sr. No.</td><td>{{ doc.serial_no or "" }}</td></tr>
      <tr><td class="lbl">Document No.</td><td>{{ doc.document_no or doc.name }}</td></tr>
      <tr><td class="lbl">Purpose Code</td><td>{{ doc.purpose_code or "" }}</td></tr>
    </table>
  </div>

  <!-- Title -->
  <div class="title-block no-break">
    <h2>FORM NO. 15CB</h2>
    <div class="rule">(See rule 37BB)</div>
    <div class="sub">Certificate of an accountant*</div>
  </div>

  <!-- Intro -->
  <div class="intro">
    <p>We have examined the agreement (wherever applicable) between</p>
    <p class="strong">{{ company_name }} (Remitter)</p>
    <p>and</p>
    <p class="strong">{{ vendor_name }} (Beneficiary)</p>
    <p style="text-align:justify; margin-top:4px;">
      requiring the above remittance as well as the relevant documents and books of account required for
      ascertaining the nature of remittance and for determining the rate of deduction of tax at source as per
      provisions of Chapter XVII-B. We hereby certify the following:&mdash;
    </p>
  </div>

  <!-- Main form table -->
  <table class="form-table">

    <!-- Row A: Beneficiary -->
    <tr>
      <td class="col-letter">A</td>
      <td colspan="2">Name and address of the beneficiary of the remittance:
        <div style="margin-top:4px;"><strong>{{ vendor_name }}</strong></div>
        <div>{{ vendor_address_full or "—" }}</div>
      </td>
    </tr>

    <!-- Row B-1: Country / Currency -->
    <tr>
      <td class="col-letter" rowspan="13">B</td>
      <td class="col-num">1</td>
      <td>
        <div class="split-2">
          <div><strong>Country to which remittance is made</strong></div>
          <div style="text-align:right;">
            <strong>Country:</strong> {{ country_label }} &nbsp;&nbsp;
            <strong>Currency:</strong> {{ currency_label }}
          </div>
        </div>
      </td>
    </tr>

    <!-- 2: Amount payable -->
    <tr>
      <td class="col-num">2</td>
      <td>
        <div class="split-2">
          <div><strong>Amount payable</strong></div>
          <div style="text-align:right;">
            In foreign currency: <strong>{{ currency_label }} {{ "{:,.2f}".format(doc.amount_payable_foreign or 0) }}</strong><br>
            In Indian: <strong>₹ {{ "{:,.2f}".format(doc.amount_payable_inr or 0) }}</strong>
            {% if doc.exchange_rate %} <span class="small">(approx) @ {{ doc.exchange_rate }}</span>{% endif %}
          </div>
        </div>
      </td>
    </tr>

    <!-- 3: Bank -->
    <tr>
      <td class="col-num">3</td>
      <td>
        <div class="split-2">
          <div><strong>Name of the bank and Branch</strong></div>
          <div style="text-align:right;">{{ bank_full }}</div>
        </div>
      </td>
    </tr>

    <!-- 4: BSR -->
    <tr>
      <td class="col-num">4</td>
      <td>
        <div class="split-2">
          <div><strong>BSR Code of the bank branch (7 digit)</strong></div>
          <div style="text-align:right;">{{ doc.bsr_code or "—" }}</div>
        </div>
      </td>
    </tr>

    <!-- 5: Proposed date -->
    <tr>
      <td class="col-num">5</td>
      <td>
        <div class="split-2">
          <div><strong>Proposed date of remittance</strong></div>
          <div style="text-align:right;">
            {{ frappe.format_value(doc.proposed_date_of_remittance, {"fieldtype": "Date"}) if doc.proposed_date_of_remittance else "—" }}
          </div>
        </div>
      </td>
    </tr>

    <!-- 6: Nature -->
    <tr>
      <td class="col-num">6</td>
      <td>
        <div class="split-2">
          <div><strong>Nature of remittance as per agreement / document</strong></div>
          <div style="text-align:right;">{{ nature_label }}</div>
        </div>
      </td>
    </tr>

    <!-- 7: Grossed up -->
    <tr>
      <td class="col-num">7</td>
      <td>
        <div class="split-2">
          <div><strong>In case the remittance is net of taxes, whether tax payable has been grossed up?</strong></div>
          <div style="text-align:right;" class="yes-no">{{ "Yes" if doc.gross_up else "No" }}</div>
        </div>
      </td>
    </tr>

    <!-- 8: Taxability under ITA -->
    <tr>
      <td class="col-num">8</td>
      <td>
        <strong>Taxability under the provisions of Income Tax Act (without considering DTAA)</strong>
        <table class="nested-list" style="margin-top:4px;">
          <tr>
            <td class="indent-1 k">(a) the relevant section of the Act under which the remittance is covered:</td>
            <td>{{ doc.section_of_act or "—" }}</td>
          </tr>
          <tr>
            <td class="indent-1 k">(b) TDS Rate as per ITA:</td>
            <td>{{ doc.tds_rate_income_tax_act or 0 }} %</td>
          </tr>
          <tr>
            <td class="indent-1 k">(c) Gross amount &amp; TDS amount:</td>
            <td>
              Gross (Foreign): <strong>{{ currency_label }} {{ "{:,.2f}".format(doc.ita_gross_amount_foreign or 0) }}</strong> &nbsp;|&nbsp;
              TDS (Foreign): <strong>{{ currency_label }} {{ "{:,.2f}".format(doc.ita_tds_amount_foreign or 0) }}</strong><br>
              Gross (INR): <strong>₹ {{ "{:,.2f}".format(doc.ita_gross_amount_inr or 0) }}</strong> &nbsp;|&nbsp;
              TDS (INR): <strong>₹ {{ "{:,.2f}".format(doc.ita_tds_amount_inr or 0) }}</strong>
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- 9: DTAA Relief -->
    <tr>
      <td class="col-num">9</td>
      <td>
        <strong>If any relief is claimed under DTAA &mdash;</strong>
        <table class="nested-list" style="margin-top:4px;">
          <tr>
            <td class="indent-1 k">(i) whether tax residency certificate is obtained from the recipient of remittance</td>
            <td class="yes-no">{{ "Yes" if doc.trc_obtained else "No" }}</td>
          </tr>
          <tr>
            <td class="indent-1 k">(ii) please specify relevant DTAA</td>
            <td>{{ doc.dtaa_name or "—" }}</td>
          </tr>
          <tr>
            <td class="indent-1 k">(ii) please specify relevant article of DTAA</td>
            <td>{{ doc.dtaa_article or doc.applicable_dtaa_article or "—" }}</td>
          </tr>
          <tr>
            <td class="indent-1 k">(iii) taxable income as per DTAA</td>
            <td>In Indian &nbsp;&nbsp; <strong>{{ "{:,.0f}".format(doc.dtaa_taxable_income or 0) }}</strong></td>
          </tr>
          <tr>
            <td class="indent-1 k">(iv) tax liability as per DTAA</td>
            <td>In Indian &nbsp;&nbsp; <strong>{{ "{:,.0f}".format(doc.dtaa_tax_liability or doc.tax_liability or 0) }}</strong></td>
          </tr>

          <!-- A. Royalties / FTS / Interest / Dividend -->
          <tr>
            <td colspan="2" style="padding-top:6px;">
              <strong>A.</strong> If the remittance is for royalties, fee for technical services, interest, dividend etc. (not connected with permanent establishment) please indicate:&mdash;
              &nbsp;&nbsp; <span class="yes-no">{{ "Yes" if (doc.applicable_dtaa_article or doc.dtaa_article) else "No" }}</span>
            </td>
          </tr>
          <tr>
            <td class="indent-2 k">(a) Article of DTAA</td>
            <td>{{ doc.applicable_dtaa_article or doc.dtaa_article or "—" }}</td>
          </tr>
          <tr>
            <td class="indent-2 k">(b) Rate of TDS required to be deducted in terms of such article of the applicable DTAA (As per DTAA %)</td>
            <td>{{ doc.tds_rate_as_per_dtaa or doc.tds_rate_dtaa or 0 }} %</td>
          </tr>

          <!-- B. Business income -->
          <tr>
            <td colspan="2" style="padding-top:6px;">
              <strong>B.</strong> In case the remittance is on account of business income, please indicate:&mdash;
              &nbsp;&nbsp; <span class="yes-no">{{ "Yes" if doc.income_taxable_in_india else "No" }}</span>
            </td>
          </tr>
          <tr>
            <td class="indent-2 k">(a) The amount of income is liable to tax in India</td>
            <td class="yes-no">{{ "Yes" if doc.income_taxable_in_india else "No" }}</td>
          </tr>
          <tr>
            <td class="indent-2 k">(b) The basis of arriving at the rate of deduction of tax</td>
            <td>{{ doc.basis_for_tax_deduction_rate or "—" }}</td>
          </tr>

          <!-- C. Capital gains -->
          <tr>
            <td colspan="2" style="padding-top:6px;">
              <strong>C.</strong> In case the remittance is on account of capital gains, please indicate:&mdash;
              &nbsp;&nbsp; <span class="yes-no">{{ "Yes" if (doc.long_term_capital_gains_amount or doc.short_term_capital_gains_amount) else "No" }}</span>
            </td>
          </tr>
          <tr>
            <td class="indent-2 k">(a) amount of long term capital gains</td>
            <td>{{ "{:,.2f}".format(doc.long_term_capital_gains_amount or 0) }}</td>
          </tr>
          <tr>
            <td class="indent-2 k">(b) amount of short-term capital gains</td>
            <td>{{ "{:,.2f}".format(doc.short_term_capital_gains_amount or 0) }}</td>
          </tr>
          <tr>
            <td class="indent-2 k">(c) basis of arriving at taxable income</td>
            <td>{{ doc.basis_for_taxable_income_calculation or "—" }}</td>
          </tr>

          <!-- D. Other -->
          <tr>
            <td colspan="2" style="padding-top:6px;">
              <strong>D.</strong> In case of other remittance not covered by sub-items A, B &amp; C
              &nbsp;&nbsp; <span class="yes-no">{{ "Yes" if doc.specify_nature_of_remittance else "No" }}</span>
            </td>
          </tr>
          <tr>
            <td class="indent-2 k">(a) Please specify nature of remittance</td>
            <td>{{ doc.specify_nature_of_remittance or "—" }}</td>
          </tr>
          <tr>
            <td class="indent-2 k">(b) Whether taxable in India as per DTAA</td>
            <td class="yes-no">{{ "Yes" if doc.taxable_in_india_as_per_dtaa else "No" }}</td>
          </tr>
          <tr>
            <td class="indent-2 k">(c) If yes, rate of TDS required to be deducted in terms of such article of applicable DTAA</td>
            <td>{{ doc.applicable_tds_rate or 0 }} %</td>
          </tr>
          <tr>
            <td class="indent-2 k">(d) if not, please furnish brief reasons thereof, specifying article of DTAA</td>
            <td>{{ doc.reason_for_non_taxability or "—" }}</td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- 10: Amount of TDS -->
    <tr>
      <td class="col-num">10</td>
      <td>
        <div class="split-2">
          <div><strong>Amount of TDS</strong></div>
          <div style="text-align:right;">
            In foreign currency: <strong>{{ "{:,.2f}".format(doc.tds_amount_foreign or 0) }}</strong><br>
            In Indian: <strong>₹ {{ "{:,.2f}".format(doc.total_tax_amount or doc.tds_amount_inr or 0) }}</strong>
            {% if doc.exchange_rate %} <span class="small">(approx) @ {{ doc.exchange_rate }}</span>{% endif %}
          </div>
        </div>
      </td>
    </tr>

    <!-- 11: Rate of TDS -->
    <tr>
      <td class="col-num">11</td>
      <td>
        <div class="split-2">
          <div><strong>Rate of TDS</strong></div>
          <div style="text-align:right;">
            As per Income Tax Act: <strong>{{ doc.tds_rate_income_tax_act or 0 }} %</strong> &nbsp;|&nbsp;
            As per DTAA: <strong>{{ doc.tds_rate_as_per_dtaa or doc.tds_rate_dtaa or 0 }} %</strong><br>
            Applied: <strong>{{ doc.applied_rate or 0 }} %</strong>
          </div>
        </div>
      </td>
    </tr>

    <!-- 12: Actual after TDS -->
    <tr>
      <td class="col-num">12</td>
      <td>
        <div class="split-2">
          <div><strong>Actual amount of remittance after TDS</strong></div>
          <div style="text-align:right;">
            In foreign currency: <strong>{{ currency_label }} {{ "{:,.2f}".format(doc.actual_amt_after_tds_foreign or 0) }}</strong><br>
            In Indian: <strong>₹ {{ "{:,.2f}".format(doc.actual_amt_after_tds_inr or 0) }}</strong>
          </div>
        </div>
      </td>
    </tr>

    <!-- 13: Date of TDS deduction -->
    <tr>
      <td class="col-num">13</td>
      <td>
        <div class="split-2">
          <div><strong>Date of deduction of tax at source, if any</strong></div>
          <div style="text-align:right;">—</div>
        </div>
      </td>
    </tr>

  </table>

  {% if doc.invoices %}
  <p style="font-weight:bold; margin-top:10px;">Invoice Details:</p>
  <table class="form-table" style="margin-top:4px;">
    <tr style="background:#dce6f1; font-weight:bold; text-align:center;">
      <td>#</td>
      <td>SAP Doc No.</td>
      <td>Invoice No.</td>
      <td>Doc Type</td>
      <td>Doc Date</td>
      <td>Amount ({{ currency_label }})</td>
      <td>Amount (INR)</td>
    </tr>
    {% for inv in doc.invoices %}
    <tr>
      <td class="center">{{ loop.index }}</td>
      <td>{{ inv.sap_document_no or "—" }}</td>
      <td>{{ inv.invoice_no or "—" }}</td>
      <td>{{ inv.document_type or "—" }}</td>
      <td>{{ frappe.format_value(inv.document_date, {"fieldtype": "Date"}) if inv.document_date else "—" }}</td>
      <td class="center">{{ "{:,.2f}".format(inv.wrshb or 0) }}</td>
      <td class="center">{{ "{:,.2f}".format(inv.dmshb or 0) }}</td>
    </tr>
    {% endfor %}
    <tr style="font-weight:bold; background:#f5f5f5;">
      <td colspan="5" style="text-align:right;">Total</td>
      <td class="center">{{ "{:,.2f}".format(doc.invoices|sum(attribute='wrshb')) }}</td>
      <td class="center">{{ "{:,.2f}".format(doc.invoices|sum(attribute='dmshb')) }}</td>
    </tr>
  </table>
  {% endif %}

  <p style="margin-top:10px; font-size:8.5pt;">
    The information given above is true and correct to the best of my knowledge and belief and is in
    accordance with the books of account, documents and other records maintained by the assessee in
    the ordinary course of business.
  </p>

  <div class="sig-block no-break">
    <div class="sig-left">
      <p><strong>Place:</strong> ___________________________</p>
      <br>
      <p><strong>Date:</strong> ____________________________</p>
    </div>
    <div class="sig-right">
      <div class="sig-line">
        Signature of the accountant<br>
        <strong>Name &amp; Address:</strong><br>
        _______________________________<br>
        _______________________________<br>
        <strong>Membership No.:</strong> ________________
      </div>
    </div>
  </div>

  <p class="small" style="margin-top:10px; color:#555;">
    * Accountant means a person referred to in the Explanation below sub-section (2) of section 288 of the Income Tax Act, 1961.
  </p>

</div>
"""


def install():
	name = "Form 15CB"
	doctype = "Remittance Form 15 CB"

	if frappe.db.exists("Print Format", name):
		pf = frappe.get_doc("Print Format", name)
		pf.doc_type = doctype
		pf.print_format_type = "Jinja"
		pf.standard = "No"
		pf.disabled = 0
		pf.html = _HTML
		pf.save(ignore_permissions=True)
		print(f"Updated Print Format: {name}")
	else:
		pf = frappe.new_doc("Print Format")
		pf.name = name
		pf.doc_type = doctype
		pf.print_format_type = "Jinja"
		pf.standard = "No"
		pf.html = _HTML
		pf.insert(ignore_permissions=True)
		print(f"Created Print Format: {name}")

	frappe.db.commit()
	print(f"\nDone. Open any {doctype} record → Menu → Print → choose 'Form 15CB'.")
