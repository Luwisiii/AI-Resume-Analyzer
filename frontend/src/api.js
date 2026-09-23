import axios from "axios";

// Empty baseURL = same origin: in dev, Vite proxies /api to Django (vite.config.js),
// so the session cookie is first-party and never crosses origins.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  withCredentials: true,
  // Django's CSRF cookie, echoed back as a header on every write.
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
  withXSRFToken: true,
});

// A session that expired or was ended elsewhere should drop us back to the
// sign-in screen rather than leave the UI retrying a request that cannot succeed.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) window.dispatchEvent(new Event("auth:expired"));
    return Promise.reject(error);
  }
);

export const errorMessage = (err, fallback = "Something went wrong. Please try again.") => {
  if (!err.response) return "Can't reach the server. Check your connection and try again.";
  if (err.response.status === 429) return "Too many attempts. Please wait a minute and try again.";

  const data = err.response.data;
  if (data?.errors) return Object.values(data.errors).join(" ");
  if (data?.error) return data.error;
  // DRF: {detail} or {field: [messages]}.
  if (data && typeof data === "object") return Object.values(data).flat().join(" ");
  return fallback;
};

export default api;
