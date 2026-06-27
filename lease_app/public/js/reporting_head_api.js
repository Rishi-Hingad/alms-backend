export async function fetchIndentData(baseUrl, requestId, token) {
    let url = `${baseUrl}/api/method/lease_app.www.reporting_head_approval.get_car_indent_data?indent_form_id=${encodeURIComponent(requestId)}`;
    if (token) {
        url += `&token=${encodeURIComponent(token)}`;
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch data");

    return await res.json();
}

export async function processIndent(baseUrl, requestId, remarks, token, action) {
    const url = `${baseUrl}/api/method/lease_app.api.car_indent_reporting_head.process_car_indent_by_reporting` +
        `?indent_form=${encodeURIComponent(requestId)}` +
        `&remarks=${encodeURIComponent(remarks)}` +
        `&token=${encodeURIComponent(token)}` +
        `&action=${encodeURIComponent(action)}`;

    const res = await fetch(url);
    const result = await res.json();

    const data = result.message;

    if (!data) {
        throw new Error("Invalid server response");
    }

    if (data.redirect_url) {
        window.location.href = data.redirect_url;
        return;
    }

    if (!data.success) {
        throw new Error(data.message || "Operation failed");
    }

    return data;
}