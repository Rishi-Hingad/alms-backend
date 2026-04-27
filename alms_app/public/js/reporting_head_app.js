console.log("🔥 reporting_head_app.js LOADED");

import { fetchIndentData, processIndent } from "./reporting_head_api.js";
import * as UI from "./reporting_head_ui.js";

document.addEventListener("DOMContentLoaded", () => {

    const search = new URLSearchParams(window.location.search);

    const CONFIG = {
        requestId: search.get("id"),
        token: search.get("token"),
        baseUrl: window.location.origin
    };

    UI.initUI(CONFIG);

    loadData(CONFIG);

    bindEvents(CONFIG);
});


async function loadData(CONFIG) {
    try {
        UI.showLoading();

        const result = await fetchIndentData(CONFIG.baseUrl, CONFIG.requestId);
        const payload = result.message;
        if (!payload.success) throw new Error(payload.message || "Failed");

        const data = payload.data;

        UI.updateUI(data);

        UI.hideLoading();
        UI.showMainContent();

    } catch (err) {
        UI.showFormError(err.message);
        UI.hideLoading();
        UI.showMainContent();
    }
}


function bindEvents(CONFIG) {

    document.getElementById("refreshBtn")
        ?.addEventListener("click", () => loadData(CONFIG));

    document.getElementById("approveBtn")
        ?.addEventListener("click", () => handleApprove(CONFIG));

    document.getElementById("rejectBtn")
        ?.addEventListener("click", () => handleReject(CONFIG));
}


async function handleApprove(CONFIG) {

    const remarks = UI.getRemarks();

    if (!UI.validateRemarks(remarks)) return;
    if (document.getElementById("approveBtn").disabled) return;

    try {
        UI.setLoadingState(true);

        const res = await processIndent(
            CONFIG.baseUrl,
            CONFIG.requestId,
            remarks,
            CONFIG.token,
            "approve"
        );

        if (res.status === "no_change") {
            UI.showFormError(res.message);
            return;
        }

        UI.showFormSuccess("Approved successfully ✅");

        loadData(CONFIG);

    } catch (err) {
        UI.showFormError(err.message);
    } finally {
        UI.setLoadingState(false);
    }
}

async function handleReject(CONFIG) {

    const remarks = UI.getRemarks();

    if (!UI.validateRemarks(remarks)) return;
    if (document.getElementById("rejectBtn").disabled) return;

    try {
        UI.setLoadingState(true);

        const res = await processIndent(
            CONFIG.baseUrl,
            CONFIG.requestId,
            remarks,
            CONFIG.token,
            "reject"
        );

        if (res.status === "no_change") {
            UI.showFormError(res.message);
            return;
        }

        UI.showFormSuccess("Rejected successfully ❌");

        loadData(CONFIG);

    } catch (err) {
        UI.showFormError(err.message);
    } finally {
        UI.setLoadingState(false);
    }
}