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
        revokeBtn: document.getElementById('revokeBtn'),
        remarksInput: document.getElementById('remarks'),
        successMessage: document.getElementById('success-message'),
        errorMessage: document.getElementById('server-error')
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
    setText('eligibility', formatCurrency(data.eligibility));
    setText('vehicle-model', data.vehicle_make_model);
    setText('ex-showroom', formatCurrency(data.net_ex_showroom_price));
    setText('finance-amount', formatCurrency(data.finance_amount));
    setText('approval-status', status);

    if (status === "Approved" || status === "Rejected") {
        document.getElementById("remarks-row").style.display = "table-row";
        setText('remarks-display', data.reporting_head_remarks);
    } else {
        document.getElementById("remarks-row").style.display = "none";
    }

    handleState(status, data.user_can_approve, data.has_previously_approved);

    const statusEl = document.getElementById('approval-status');
    statusEl.className = `approval-status badge ${(status || 'pending').toLowerCase()}`;
}

function handleState(status, userCanApprove, hasPreviouslyApproved) {
    const approveBtn = elements.approveBtn;
    const rejectBtn = elements.rejectBtn;
    const revokeBtn = elements.revokeBtn;
    const remarksInput = elements.remarksInput;

    // Default to hiding unless they can approve
    approveBtn.style.display = "none";
    rejectBtn.style.display = "none";
    if (revokeBtn) revokeBtn.style.display = "none";
    remarksInput.disabled = true;

    hideAlreadyApproved();

    if (status === "Approved" || status === "Rejected" || status.includes("Rejected by")) {
        showAlreadyApproved(status);
        return;
    }

    if (userCanApprove) {
        approveBtn.style.display = "inline-block";
        rejectBtn.style.display = "inline-block";
        approveBtn.disabled = false;
        rejectBtn.disabled = false;
        remarksInput.disabled = false;
    } else if (hasPreviouslyApproved) {
        // They approved previously but the document is still pending overall
        if (revokeBtn) {
            revokeBtn.style.display = "inline-block";
            revokeBtn.disabled = false;
            remarksInput.disabled = false;
        }
    } else {
        const notice = document.getElementById("already-approved-notice");
        const details = document.getElementById("approval-details");
        if (notice && details) {
            notice.className = "already-approved-notice pending";
            details.innerHTML = "You are not authorized to approve this request at this time.<br>Please ensure you are logged into the ALMS portal.";
            notice.style.display = "block";
        }
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

    if (status === "Approved" || status.includes("Approved")) {
        notice.classList.add("approved");
        details.textContent = "This request has been approved.";
    }

    if (status === "Rejected" || status.includes("Rejected")) {
        notice.classList.add("rejected");
        details.textContent = "This request has been rejected.";
    }

    notice.style.display = "block";
}

function hideAlreadyApproved() {
    const notice = document.getElementById("already-approved-notice");
    if (notice) notice.style.display = "none";
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined || amount === '') return '-';
    const num = Number(amount);
    if (isNaN(num)) return amount;
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
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
    if (elements.revokeBtn) elements.revokeBtn.disabled = loading;

    elements.approveBtn.textContent = loading ? "Processing..." : "Approve Request";
    elements.rejectBtn.textContent = loading ? "Processing..." : "Reject Request";
    if (elements.revokeBtn) elements.revokeBtn.textContent = loading ? "Processing..." : "Revoke & Reject";
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