// remittance_utils.js
// Shared utility for Remittance listviews.
// Included via hooks.py → app.bundle.js (or app_include_js).
// Do NOT wrap in frappe.listview_settings — this is a plain namespace.

window.RemittanceUtils = window.RemittanceUtils || {};

RemittanceUtils.attachButtons = function (listview) {
	if (!frappe.user.has_role("Remittance User")) return;

	// ── Button 1: Fetch from SAP ──────────────────────────────────────────────
	listview.page.add_inner_button(__("Fetch from SAP"), function () {
		let dialog = new frappe.ui.Dialog({
			title: __("Fetch Vendor Line Items from SAP"),
			fields: [
				{
					fieldname: "company",
					fieldtype: "Link",
					label: __("Company"),
					options: "Remittance Company",
					reqd: 1,
				},
				{
					fieldname: "vendor",
					fieldtype: "Link",
					label: __("Vendor"),
					options: "Remittance Vendor",
					reqd: 1,
				},
				{
					fieldname: "augdt",
					fieldtype: "Date",
					label: __("Open Invoices as on"),
					reqd: 1,
					default: frappe.datetime.get_today(),
				},
			],
			primary_action_label: __("Fetch"),
			primary_action(values) {
				frappe.db
					.get_value("Remittance Company", values.company, [
						"company_code",
						"sap_client_code",
					])
					.then((comp) => {
						if (!comp.message || !comp.message.company_code) {
							frappe.throw(__("Company Code not found for selected company"));
						}

						const bukrs = comp.message.company_code;
						const sap_client = comp.message.sap_client_code || "";

						frappe.db
							.get_value("Remittance Vendor", values.vendor, ["vendor_code"])
							.then((vend) => {
								if (!vend.message || !vend.message.vendor_code) {
									frappe.throw(__("Vendor Code not found for selected vendor"));
								}

								const lifnr = vend.message.vendor_code;
								const augdt = frappe.datetime
									.str_to_obj(values.augdt)
									.toISOString()
									.slice(0, 10)
									.replaceAll("-", "");

								frappe.call({
									method: "remittance_tool.remittance_tool.api.v1.fetch_sap_data.fetch_sap_data",
									args: { lifnr, bukrs, augdt, sap_client },
									freeze: true,
									freeze_message: __("Fetching data from SAP..."),
									callback: function (r) {
										if (!r.exc && r.message) {
											frappe.msgprint({
												title: __("Success"),
												message: r.message.message,
												indicator: "green",
											});
											dialog.hide();
											listview.refresh();
										}
									},
								});
							});
					});
			},
		});
		dialog.show();
	});

	// ── Button 2: Make Form 15 CB ─────────────────────────────────────────────
	listview.page.add_inner_button(__("Make Form 15 CB"), function () {
		let make_dialog = new frappe.ui.Dialog({
			title: __("Create Form 15 CB from RE KR Entries"),
			size: "extra-large",
			fields: [
				{
					fieldname: "company",
					fieldtype: "Link",
					label: __("Company"),
					options: "Remittance Company",
					reqd: 1,
				},
				{
					fieldname: "vendor",
					fieldtype: "Link",
					label: __("Vendor"),
					options: "Remittance Vendor",
					reqd: 1,
				},
				{
					fieldname: "from_date",
					fieldtype: "Date",
					label: __("From Posting Date"),
				},
				{
					fieldname: "to_date",
					fieldtype: "Date",
					label: __("To Posting Date"),
				},
				{
					fieldname: "posting_dates_help",
					fieldtype: "HTML",
					options:
						'<div class="text-muted small" style="margin:-6px 0 8px;">' +
						__("Leave both blank to load all unused entries. Pick a range to scope the dates. Only entries that share the same Exchange Rate & Tax Rate can be combined into a single Form 15 CB.") +
						"</div>",
				},
				{
					fieldname: "get_entries_btn",
					fieldtype: "Button",
					label: __("Get Entries"),
					click: function () {
						RemittanceUtils._fetchEntries(make_dialog);
					},
				},
				{
					fieldname: "entries_section",
					fieldtype: "Section Break",
					label: __("RE KR Entries"),
				},
				{
					fieldname: "entries_html",
					fieldtype: "HTML",
					label: __("Entries"),
				},
			],
			primary_action_label: __("Create Form 15 CB"),
			primary_action: function () {
				RemittanceUtils._create15CB(make_dialog, listview);
			},
		});

		// Disable primary button until entries are loaded
		make_dialog.$wrapper.find(".btn-primary-dark, .btn-primary").prop("disabled", true);
		make_dialog.show();
	});
};

// ── Internal: Fetch FBL1N entries ─────────────────────────────────────────────
RemittanceUtils._fetchEntries = function (dlg) {
	const company = dlg.get_value("company");
	const vendor = dlg.get_value("vendor");
	const from_date = dlg.get_value("from_date");
	const to_date = dlg.get_value("to_date");

	if (!company || !vendor) {
		frappe.msgprint(__("Please select Company and Vendor first"));
		return;
	}

	if (from_date && to_date && from_date > to_date) {
		frappe.msgprint(__("From Posting Date cannot be after To Posting Date"));
		return;
	}

	frappe.db.get_value("Remittance Company", company, ["company_code"]).then((comp) => {
		const bukrs = comp.message.company_code;

		frappe.db.get_value("Remittance Vendor", vendor, ["vendor_code"]).then((vend) => {
			const lifnr = vend.message.vendor_code;

			frappe.call({
				method: "remittance_tool.remittance_tool.api.v1.create_form_15cb.get_fbl1n_entries",
				args: { bukrs, lifnr, from_date, to_date },
				freeze: true,
				freeze_message: __("Loading entries..."),
				callback: function (r) {
					if (r.message && r.message.length) {
						RemittanceUtils._renderEntries(dlg, r.message);
						dlg.$wrapper
							.find(".btn-primary-dark, .btn-primary")
							.prop("disabled", false);
					} else {
						dlg.fields_dict.entries_html.$wrapper.html(
							'<p class="text-muted">' +
								__("No RE KR entries found for this filter.") +
								"</p>"
						);
						dlg.$wrapper
							.find(".btn-primary-dark, .btn-primary")
							.prop("disabled", true);
					}
				},
			});
		});
	});
};

// ── Internal: Render entries as a checkable table ─────────────────────────────
RemittanceUtils._renderEntries = function (dlg, entries) {
	// Compute derived fields
	entries.forEach((e) => {
		e._rate = e.qsshb && e.qbshb ? (e.qbshb / e.qsshb) * 100 : 0;
		e._kurse = e.kurse || 0;
	});

	// Group by (exchange_rate, tax_rate) — round to 4 dp to avoid float drift
	const groups = {};
	entries.forEach((e) => {
		const key = `${e._kurse.toFixed(4)}|${e._rate.toFixed(4)}`;
		(groups[key] = groups[key] || []).push(e);
	});

	// Pre-select the largest group that has a non-zero tax rate
	let bestKey = null,
		bestSize = 0;
	Object.entries(groups).forEach(([key, arr]) => {
		const rate = parseFloat(key.split("|")[1]);
		if (rate > 0 && arr.length > bestSize) {
			bestSize = arr.length;
			bestKey = key;
		}
	});
	// Fallback: largest group overall
	if (!bestKey) {
		Object.entries(groups).forEach(([key, arr]) => {
			if (arr.length > bestSize) {
				bestSize = arr.length;
				bestKey = key;
			}
		});
	}

	let html = `
		<div class="mb-2">
			<label>
				<input type="checkbox" class="fbl1n-select-all">
				<strong>${__("Select All")}</strong>
			</label>
			<span class="ml-3 text-muted small">
				${__("Auto-selected entries share the same Exchange Rate & Tax Rate (qbshb/qsshb).")}
			</span>
		</div>
		<div style="max-height:400px; overflow-y:auto;">
		<table class="table table-bordered table-sm">
			<thead>
				<tr>
					<th style="width:30px;"></th>
					<th>${__("Document No")}</th>
					<th>${__("Reference")}</th>
					<th>${__("Doc Type")}</th>
					<th>${__("Doc Date")}</th>
					<th>${__("Posting Date")}</th>
					<th style="text-align:right;">${__("WHT Base")}</th>
					<th style="text-align:right;">${__("WHT Amt")}</th>
					<th style="text-align:right;">${__("Tax Rate %")}</th>
					<th style="text-align:right;">${__("Amount")}</th>
					<th>${__("Currency")}</th>
					<th style="text-align:right;">${__("Exchange Rate")}</th>
				</tr>
			</thead>
			<tbody>`;

	entries.forEach((e) => {
		const key = `${e._kurse.toFixed(4)}|${e._rate.toFixed(4)}`;
		const checked = key === bestKey ? "checked" : "";
		const highlight = key === bestKey ? ' style="background:#e6f7e6;"' : "";

		html += `
			<tr${highlight}>
				<td><input type="checkbox" class="fbl1n-check"
					data-name="${e.name}"
					data-kurse="${e._kurse}"
					data-rate="${e._rate}" ${checked}></td>
				<td>${e.belnr || ""}</td>
				<td>${e.xblnr || ""}</td>
				<td>${e.blart || ""}</td>
				<td>${e.bldat || ""}</td>
				<td>${e.budat || ""}</td>
				<td style="text-align:right;">${(e.qsshb || 0).toFixed(2)}</td>
				<td style="text-align:right;">${(e.qbshb || 0).toFixed(2)}</td>
				<td style="text-align:right;">${e._rate.toFixed(2)}</td>
				<td style="text-align:right;">${Math.abs(e.wrshb || 0).toFixed(2)}</td>
				<td>${e.waers || ""}</td>
				<td style="text-align:right;">${e._kurse.toFixed(5)}</td>
			</tr>`;
	});

	html += "</tbody></table></div>";

	dlg.fields_dict.entries_html.$wrapper.html(html);

	// Select-all toggle
	dlg.$wrapper.find(".fbl1n-select-all").on("change", function () {
		dlg.$wrapper.find(".fbl1n-check").prop("checked", $(this).is(":checked"));
	});
};

// ── Internal: Create Form 15 CB from checked entries ─────────────────────────
RemittanceUtils._create15CB = function (dlg, lv) {
	const company = dlg.get_value("company");
	const vendor = dlg.get_value("vendor");

	const selected = [];
	const meta = []; // { name, kurse, rate }

	dlg.$wrapper.find(".fbl1n-check:checked").each(function () {
		const $cb = $(this);
		const name = $cb.data("name");
		selected.push(name);
		meta.push({
			name: name,
			kurse: parseFloat($cb.data("kurse")) || 0,
			rate: parseFloat($cb.data("rate")) || 0,
		});
	});

	if (!selected.length) {
		frappe.msgprint(__("Please select at least one entry"));
		return;
	}

	function proceed_to_create() {
		frappe.call({
			method: "remittance_tool.remittance_tool.api.v1.create_form_15cb.create_form_15cb",
			args: {
				company: company,
				vendor: vendor,
				selected_entries: JSON.stringify(selected),
			},
			freeze: true,
			freeze_message: __("Creating Form 15 CB..."),
			callback: function (r) {
				if (!r.exc && r.message) {
					dlg.hide();
					frappe.set_route("Form", "Remittance Form 15 CB", r.message.name);
				}
			},
		});
	}

	// Warn if selected entries have mismatched Exchange Rate or Tax Rate
	const base = meta[0];
	const mismatched = meta.some(
		(m) => Math.abs(m.kurse - base.kurse) > 0.0001 || Math.abs(m.rate - base.rate) > 0.0001
	);

	if (!mismatched) {
		proceed_to_create();
		return;
	}

	// Build mismatch warning dialog
	const rows = meta
		.map(
			(m) =>
				`<tr>
					<td>${frappe.utils.escape_html(m.name)}</td>
					<td style="text-align:right;">${m.kurse.toFixed(5)}</td>
					<td style="text-align:right;">${m.rate.toFixed(2)}%</td>
				</tr>`
		)
		.join("");

	const warn_html = `
		<div style="font-size:13px;">
			<p style="color:#c0392b; font-weight:600; margin-bottom:8px;">
				${__("Selected entries have different Exchange Rate or Tax Rate.")}
			</p>
			<p style="margin-bottom:10px;">
				${__(
					"A Form 15CB usually contains entries that share the same rates. Please review the values below:"
				)}
			</p>
			<table class="table table-bordered table-sm" style="font-size:12px; margin:0;">
				<thead style="background:#f5f5f5;">
					<tr>
						<th>${__("Entry")}</th>
						<th style="text-align:right;">${__("Exchange Rate")}</th>
						<th style="text-align:right;">${__("Tax Rate")}</th>
					</tr>
				</thead>
				<tbody>${rows}</tbody>
			</table>
		</div>`;

	const warn_dialog = new frappe.ui.Dialog({
		title: __("Rate Mismatch Detected"),
		fields: [{ fieldtype: "HTML", fieldname: "warn_html" }],
		// primary_action_label: __("Continue Anyway"),
		// primary_action: function () {
		// 	warn_dialog.hide();
		// 	proceed_to_create();
		// },
		// secondary_action_label: __("Cancel"),
		// secondary_action: function () {
		// 	warn_dialog.hide();
		// },
		primary_action_label: __("Cancel"),
		primary_action: function () {
			warn_dialog.hide();
		},
	});
	warn_dialog.fields_dict.warn_html.$wrapper.html(warn_html);
	warn_dialog.show();
};
