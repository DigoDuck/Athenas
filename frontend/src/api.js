// Thin wrapper over fetch for the JSON API. Errors carry a readable message.
async function request(method, url, body) {
  const response = await fetch(url, {
    method,
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(errorMessage(data, response.status));
  return data;
}

function errorMessage(data, status) {
  if (!data) return `Erro ${status}.`;
  if (data.detail) return data.detail;
  return Object.values(data).flat().join(" ");
}

export const api = {
  get: (url) => request("GET", url),
  post: (url, body) => request("POST", url, body ?? {}),
  patch: (url, body) => request("PATCH", url, body),
  delete: (url) => request("DELETE", url),
};
