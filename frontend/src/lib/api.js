const getBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl !== undefined && envUrl !== null && envUrl.trim() !== "") {
    return envUrl.trim().replace(/\/$/, "");
  }
  if (import.meta.env.PROD) {
    return "/api";
  }
  return "http://localhost:8000";
};

const API_URL = getBaseUrl();
const TOKEN_KEY = "ravisn_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let msg = "Invalid email or password";
    if (typeof data.detail === "string") {
      msg = data.detail;
    } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      msg = data.detail[0].msg;
    }
    throw new Error(msg);
  }
  return data;
}

export const api = {
  signup: (payload) => request("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/auth/me"),
  listKnowledge: () => request("/knowledge"),
  addKnowledge: (payload) => request("/knowledge", { method: "POST", body: JSON.stringify(payload) }),
  deleteKnowledge: (id) => request(`/knowledge/${id}`, { method: "DELETE" }),
  connectWhatsAppOfficial: (payload) =>
    request("/whatsapp/official/connect", { method: "POST", body: JSON.stringify(payload) }),
  startWhatsAppQr: () => request("/whatsapp/qr/start", { method: "POST" }),
  getWhatsAppQrStatus: () => request("/whatsapp/qr/status"),
  disconnectWhatsAppQr: () => request("/whatsapp/qr/disconnect", { method: "POST" }),
  connectFacebook: (payload) => request("/facebook/connect", { method: "POST", body: JSON.stringify(payload) }),
  connectInstagram: (payload) => request("/instagram/connect", { method: "POST", body: JSON.stringify(payload) }),
  listConversations: (channel) => request(`/conversations?channel=${channel}`),
  listMessages: (conversationId) => request(`/conversations/${conversationId}/messages`),
  listBookings: (channel) => request(`/bookings?channel=${channel}`),
  getApiKey: () => request("/settings/api-key"),
  saveApiKey: (openai_api_key) =>
    request("/settings/api-key", { method: "POST", body: JSON.stringify({ openai_api_key }) }),
  listChannels: () => request("/channels"),
  disconnectChannel: (connectionId) =>
    request(`/channels/${connectionId}/disconnect`, { method: "POST" }),
};
