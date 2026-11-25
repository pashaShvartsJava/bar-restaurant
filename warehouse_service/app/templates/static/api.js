function getCookie(name) {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith(name + "="))
        ?.split("=")[1];
}

async function apiFetch(url, options = {}) {
    const csrf = getCookie("csrf_token");
    console.log("CSRF FROM JS:", csrf);

    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            "X-CSRF-Token": csrf,
        },
    });
}