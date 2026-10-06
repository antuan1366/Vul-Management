const API_BASE_URL = "http://127.0.0.1:8000";


function formatApiErrorDetail(detail) {
    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail)) {
        return detail.map((item) => {
            if (typeof item === "string") return item;
            if (item?.msg) return item.msg;
            return JSON.stringify(item);
        }).join("; ");
    }

    if (detail && typeof detail === "object") {
        if (detail.message) return String(detail.message);
        if (detail.msg) return String(detail.msg);
        return JSON.stringify(detail);
    }

    return String(detail);
}


async function apiRequest(endpoint, options = {}) {
    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        }
    );

    if (!response.ok) {
        let errorMessage = `API request failed: ${response.status}`;

        try {
            const errorData = await response.json();

            if (errorData.detail !== undefined && errorData.detail !== null) {
                errorMessage = formatApiErrorDetail(errorData.detail);
            }
        } catch (error) {
            // Ignore JSON parsing errors.
        }

        throw new Error(errorMessage);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}


async function healthCheck() {
    return apiRequest("/api/health");
}