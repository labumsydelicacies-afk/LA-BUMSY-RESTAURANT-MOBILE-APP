import axios from "axios";

const isLocalHost =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE_URL = isLocalHost
  ? "http://localhost:8000"
  : import.meta.env.VITE_API_URL || "http://localhost:8000";

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const requestUrl = String(error.config?.url || "");
    const isAuthRequest =
      requestUrl.includes("/auth/login") ||
      requestUrl.includes("/auth/register") ||
      requestUrl.includes("/auth/verify-otp");

    if (status === 401) {
      localStorage.removeItem("token");
      const path = window.location.pathname;
      const onAuthPage = path === "/login" || path === "/register";
      if (!onAuthPage && !isAuthRequest) {
        window.location.assign("/login");
      }
    }
    if (!status || status >= 500) {
      window.dispatchEvent(
        new CustomEvent("app:toast", {
          detail: { message: "Server error. Please try again." },
        })
      );
    }
    return Promise.reject(error);
  }
);

axiosInstance.getBaseUrl = () => API_BASE_URL;

export default axiosInstance;
