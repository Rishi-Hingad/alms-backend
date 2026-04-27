let elements = {};
let isApproved = false;

export function initUI(CONFIG) {
    document.getElementById("indent_form").value = CONFIG.requestId;
    document.getElementById("page-title-id").textContent = CONFIG.requestId;

    elements = {
        loadingIndicator: document.getElementById('loadingIndicator'),
        mainContent: document.getElementById('mainContent'),
        approveBtn: document.getElementById('approveBtn'),
        rejectBtn: document.getElementById('rejectBtn'),
        remarksInput: document.getElementById('remarks'),
        successMessage: document.getElementById('success-message'),
        errorMessage: document.getElementById('error-message')
    };
    hideAlreadyApproved();
}

export function updateUI(data) {

    isApproved = data.is_approved;
    const status = data.reporting_head_approval || "Pending";

    setText('company-name', data.company_name);
    setText('employee-name', data.employee_name);
    setText('employee-email', data.employee_email);
    setText('designation', data.designation);
    setText('reporting-head', data.reporting_head_name);
    setText('eligibility', data.eligibility ? `₹${data.eligibility}` : '-');
    setText('vehicle-model', data.vehicle_make_model);
    setText('ex-showroom', data.net_ex_showroom_price ? `₹${data.net_ex_showroom_price}` : '-');
    setText('finance-amount', data.finance_amount ? `₹${data.finance_amount}` : '-');
    setText('approval-status', status);

    if (status === "Approved" || status === "Rejected") {
        document.getElementById("remarks-row").style.display = "table-row";
        setText('remarks-display', data.reporting_head_remarks);
    } else {
        document.getElementById("remarks-row").style.display = "none";
    }

    handleState(status);

    const statusEl = document.getElementById('approval-status');
    statusEl.className = `approval-status badge ${(data.reporting_head_approval || 'pending').toLowerCase()}`;
}

function handleState(status) {
    const approveBtn = elements.approveBtn;
    const rejectBtn = elements.rejectBtn;

    // Reset first (important)
    approveBtn.style.display = "inline-block";
    rejectBtn.style.display = "inline-block";

    approveBtn.disabled = false;
    rejectBtn.disabled = false;

    hideAlreadyApproved();

    if (status === "Approved") {
        approveBtn.style.display = "none";
        showAlreadyApproved(status);
    }

    if (status === "Rejected") {
        rejectBtn.style.display = "none";
        showAlreadyApproved(status);
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || '-';
}

function showAlreadyApproved(status) {
    const notice = document.getElementById("already-approved-notice");
    const details = document.getElementById("approval-details");

    if (!notice || !details) return;

    notice.classList.remove("approved", "rejected");

    if (status === "Approved") {
        notice.classList.add("approved");
        details.textContent = "This request is already approved. You can still change your decision.";
    }

    if (status === "Rejected") {
        notice.classList.add("rejected");
        details.textContent = "This request is already rejected. You can still change your decision.";
    }

    notice.style.display = "block";
}

function hideAlreadyApproved() {
    const notice = document.getElementById("already-approved-notice");
    if (notice) notice.style.display = "none";
}

export function getRemarks() {
    return elements.remarksInput.value.trim();
}

export function validateRemarks(val) {
    if (!val) {
        alert("Remarks required");
        return false;
    }
    return true;
}

export function disableForm() {
    elements.approveBtn.disabled = true;
    elements.rejectBtn.disabled = true;
}

export function enableForm() {
    elements.approveBtn.disabled = false;
    elements.rejectBtn.disabled = false;
}

export function setLoadingState(loading) {
    elements.approveBtn.disabled = loading;
    elements.rejectBtn.disabled = loading;

    elements.approveBtn.textContent = loading ? "Processing..." : "Approve Request";
    elements.rejectBtn.textContent = loading ? "Processing..." : "Reject Request";
}

export function showFormSuccess(msg) {
    elements.successMessage.textContent = msg;
    elements.successMessage.style.display = "block";
}

export function showFormError(msg) {
    elements.errorMessage.textContent = msg;
    elements.errorMessage.style.display = "block";
}

export function showLoading() {
    elements.loadingIndicator.style.display = "block";
}

export function hideLoading() {
    elements.loadingIndicator.style.display = "none";
}

export function showMainContent() {
    elements.mainContent.style.display = "block";
}