// Thin wrapper over fetch for the JSON API. Errors carry a readable message.
// Writes send the CSRF token from the cookie that /api/auth/me/ sets (DECISIONS.md D-044).
const csrfToken = () => document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)?.[1] ?? "";

async function request(method, url, body) {
  const headers = method === "GET" ? {} : { "X-CSRFToken": csrfToken() };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(url, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(errorMessage(data, response.status));
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

function errorMessage(data, status) {
  if (!data) return `Erro ${status}.`;
  if (data.detail) return data.detail;
  if (data.errors) return data.errors.join(" ");
  return Object.values(data).flat().join(" ");
}

export const api = {
  get: (url) => request("GET", url),
  post: (url, body) => request("POST", url, body ?? {}),
  put: (url, body) => request("PUT", url, body),
  patch: (url, body) => request("PATCH", url, body),
  delete: (url) => request("DELETE", url),
};
