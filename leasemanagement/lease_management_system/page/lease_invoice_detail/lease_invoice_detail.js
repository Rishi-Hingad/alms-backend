/* global open_invoice_dialog */
frappe.pages["lease-invoice-detail"].on_page_load = function (wrapper) {
	// var page = frappe.ui.make_app_page({
	// 	parent: wrapper,
	// 	title: 'Lease LMS Invoice Details',
	// 	single_column: true
	// });
	// frappe.ui.make_app_page({
	//     parent: wrapper,
	//     title: 'Add Lease Invoice',
	//     single_column: true
	// });

	// Show dialog after short delay
	// setTimeout(() => {
	//     if (typeof open_invoice_dialog === "function") {
	//         open_invoice_dialog();
	//     } else {
	//         frappe.msgprint("Dialog function not found.");
	//     }
	// }, 300);

	// Clear the wrapper to avoid leftovers from previous loads
	$(wrapper).empty();

	// Create the page object
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Add Lease Invoice",
		single_column: true,
	});

	// Add a primary button in the header (recommended Frappe way)
	page.set_primary_action("➕ Add New Invoice", function () {
		if (typeof open_invoice_dialog === "function") {
			open_invoice_dialog();
		} else {
			frappe.msgprint("Dialog function not found.");
		}
	});

	// Optional: You can also append content to the body
	$(page.body).append(`
        <div style="padding: 20px; max-width: 900px; margin: auto;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0;">
                <p style="color: #555;"><center>You can click the <b>"Add New Invoice"</b> button above to open the invoice dialog.</center></p>
            </div>
        </div>
    `);

	// Just for demo: define the function if it's not defined
	if (typeof open_invoice_dialog !== "function") {
		window.open_invoice_dialog = function () {
			frappe.msgprint("This is where your invoice dialog would open.");
		};
	}
	//====================================
	// Primary CTA Button in Header
	// page.set_primary_action('➕ Add New Invoice', function () {
	//     if (typeof open_invoice_dialog === "function") {
	//         open_invoice_dialog();
	//     } else {
	//         frappe.msgprint("Dialog function not found.");
	//     }
	// });

	// // 🎨 Enhanced Content UI
	// const content_html = `
	//     <div class="invoice-page-content" style="padding: 20px; max-width: 900px; margin: auto;">

	//         <div class="intro-message" style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0;">
	//             <h3 style="margin-top: 0;">Welcome to Lease Invoice Management</h3>
	//             <p style="color: #555;">This page allows you to easily add and track lease invoices for your vendors or clients.
	//             Click the <strong>Add New Invoice</strong> button above to get started.</p>
	//         </div>

	//         <div class="how-to" style="margin-top: 30px;">
	//             <h4>💡 How it works</h4>
	//             <ul style="color: #444;">
	//                 <li>Click "Add New Invoice" to open the input dialog.</li>
	//                 <li>Fill in the invoice details such as vendor, lease period, and amount.</li>
	//                 <li>Submit the form to save and track it in the system.</li>
	//             </ul>
	//         </div>

	//     </div>
	// `;

	// $(page.body).append(content_html);

	// // ✅ Temp: Define the dialog function for demo if not yet loaded
	// if (typeof open_invoice_dialog !== "function") {
	//     window.open_invoice_dialog = function() {
	//         frappe.msgprint("Invoice dialog would be shown here.");
	//     };
	// }
	//====================================
	// const page = frappe.ui.make_app_page({
	//     parent: wrapper,
	//     title: 'Lease LMS Invoice Details',
	//     single_column: true
	// });

	// let leaseData = null;
	// let invoiceTable = null;

	// $(page.body).html(`
	//     <div class="mb-4">
	//         <div class="form-group">
	//             <label>Lease ID</label>
	//             <input type="text" class="form-control" id="lease_id_input" placeholder="Enter Lease ID">
	//         </div>
	//         <button class="btn btn-primary mt-2" id="load_lease_btn">Load Lease</button>
	//     </div>

	//     <div id="lease_info" style="display: none;">
	//         <p><strong>Agreement Start Date:</strong> <span id="start_date"></span></p>
	//         <p><strong>Agreement End Date:</strong> <span id="end_date"></span></p>

	//         <h4>Previous Invoices</h4>
	//         <table class="table table-bordered">
	//             <thead>
	//                 <tr>
	//                     <th>Month</th>
	//                     <th>From</th>
	//                     <th>To</th>
	//                     <th>Amount</th>
	//                     <th>Status</th>
	//                 </tr>
	//             </thead>
	//             <tbody id="invoice_list">
	//                 <tr><td colspan="5" class="text-muted text-center">No data</td></tr>
	//             </tbody>
	//         </table>

	//         <h4>Add New Invoice</h4>
	//         <div class="form-row">
	//             <div class="form-group col-md-4">
	//                 <label>Month</label>
	//                 <select class="form-control" id="month_select">
	//                     <option>January</option><option>February</option><option>March</option>
	//                     <option>April</option><option>May</option><option>June</option>
	//                     <option>July</option><option>August</option><option>September</option>
	//                     <option>October</option><option>November</option><option>December</option>
	//                 </select>
	//             </div>
	//             <div class="form-group col-md-4">
	//                 <label>From Date</label>
	//                 <input type="date" class="form-control" id="from_date_input">
	//             </div>
	//             <div class="form-group col-md-4">
	//                 <label>To Date</label>
	//                 <input type="date" class="form-control" id="to_date_input">
	//             </div>
	//         </div>

	//         <div class="form-row">
	//             <div class="form-group col-md-6">
	//                 <label>Amount</label>
	//                 <input type="number" class="form-control" id="amount_input">
	//             </div>
	//             <div class="form-group col-md-6">
	//                 <label>With Tax</label>
	//                 <input type="checkbox" class="form-check-input ml-2" id="with_tax_input">
	//             </div>
	//         </div>

	//         <div class="form-group">
	//             <label>Tax (%)</label>
	//             <input type="number" class="form-control" id="tax_input">
	//         </div>

	//         <div class="form-group">
	//             <label>Invoice Attachment</label>
	//             <input type="file" class="form-control-file" id="invoice_attachment_input">
	//         </div>

	//         <button class="btn btn-success mt-3" id="save_invoice_btn">Save Invoice</button>
	//     </div>
	// `);

	// $('#load_lease_btn').on('click', () => {
	//     const leaseId = $('#lease_id_input').val();
	//     if (!leaseId) {
	//         frappe.msgprint("Please enter a Lease ID.");
	//         return;
	//     }

	//     frappe.db.get_doc("Lease Management", leaseId).then(doc => {
	//         leaseData = doc;
	//         $('#lease_info').show();
	//         $('#start_date').text(doc.agreement_start_date);
	//         $('#end_date').text(doc.agreement_end_date);

	//         const invoices = doc.invoice_details || [];
	//         const $tableBody = $('#invoice_list').empty();

	//         if (invoices.length === 0) {
	//             $tableBody.append(`<tr><td colspan="5" class="text-muted text-center">No Invoices</td></tr>`);
	//         } else {
	//             invoices.forEach(row => {
	//                 $tableBody.append(`
	//                     <tr>
	//                         <td>${row.month}</td>
	//                         <td>${row.from_date}</td>
	//                         <td>${row.to_date}</td>
	//                         <td>${row.amount}</td>
	//                         <td>${row.payment_status || 'Unpaid'}</td>
	//                     </tr>
	//                 `);
	//             });
	//         }
	//     }).catch(err => {
	//         frappe.msgprint("Lease not found.");
	//     });
	// });

	// $('#save_invoice_btn').on('click', async () => {
	//     const month = $('#month_select').val();
	//     const from_date = $('#from_date_input').val();
	//     const to_date = $('#to_date_input').val();
	//     const amount = parseFloat($('#amount_input').val());
	//     const with_tax = $('#with_tax_input').is(':checked') ? 1 : 0;
	//     const tax = parseFloat($('#tax_input').val()) || 0;

	//     if (!month || !from_date || !to_date || !amount) {
	//         frappe.msgprint("Please fill in all required fields.");
	//         return;
	//     }

	//     const new_row = {
	//         month, from_date, to_date, amount, with_tax, tax,
	//         invoice_attachment: "", // Optional: implement file upload
	//         custom_row_id: `row-${Date.now()}`
	//     };

	//     leaseData.invoice_details = leaseData.invoice_details || [];
	//     leaseData.invoice_details.push(new_row);

	//     frappe.db.set_value('Lease Management', leaseData.name, {
	//         invoice_details: leaseData.invoice_details
	//     }).then(() => {
	//         frappe.msgprint("Invoice added.");
	//         $('#load_lease_btn').click();  // reload data
	//     }).catch(() => {
	//         frappe.msgprint("Failed to save invoice.");
	//     });
	// });
};
