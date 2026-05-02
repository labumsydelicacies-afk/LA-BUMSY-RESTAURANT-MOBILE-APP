import { create } from "zustand";
import axiosInstance from "../api/axiosInstance";

function decodeJwt(token) {
  try {
    const payload = token.split(".")[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    return decoded;
  } catch {
    return null;
  }
}

function mapRole(rawRole) {
  if (!rawRole) return "user";
  const role = String(rawRole).toLowerCase();
  if (role.includes("admin")) return "admin";
  if (role.includes("rider")) return "rider";
  if (role.includes("customer") || role.includes("user")) return "user";
  return "user";
}

export const useAuthStore = create((set, get) => ({
  token: localStorage.getItem("token"),
  user: null,
  role: null,
  isAuthenticated: false,

  initialize: () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    const payload = decodeJwt(token);
    if (!payload || (payload.exp && payload.exp * 1000 < Date.now())) {
      localStorage.removeItem("token");
      set({ token: null, user: null, role: null, isAuthenticated: false });
      return;
    }
    set({
      token,
      user: { 
        email: payload.sub, 
        id: payload.user_id, 
        nickname: payload.nickname,
        userState: payload.user_state || "ACTIVE",
        phone: payload.phone || "",
        address: payload.address || ""
      },
      role: mapRole(payload.role),
      isAuthenticated: true,
    });
  },

  login: async (email, password) => {
    const { data } = await axiosInstance.post("/auth/login", { email, password });
    const token = data.access_token;
    const payload = decodeJwt(token);
    localStorage.setItem("token", token);
    set({
      token,
      role: mapRole(data.role ?? payload?.role),
      user: {
        email: payload?.sub ?? email,
        id: payload?.user_id ?? null,
        nickname: data.nickname ?? payload?.nickname ?? "",
        userState: data.user_state ?? payload?.user_state ?? "ACTIVE",
        phone: data.phone ?? payload?.phone ?? "",
        address: data.address ?? payload?.address ?? ""
      },
      isAuthenticated: true,
    });
    return get().role;
  },

  register: async (payload) => {
    const { data } = await axiosInstance.post("/auth/register", payload);
    return data.user ?? data;
  },

  verifyOtp: async (userId, otp) => {
    await axiosInstance.post("/auth/verify-otp", { user_id: userId, otp });
  },

  resendOtp: async (email) => {
    const { data } = await axiosInstance.post("/auth/resend-otp", { email });
    return data;
  },

  forgotPassword: async (email) => {
    const { data } = await axiosInstance.post("/auth/forgot-password", { email });
    return data;
  },

  resetPassword: async ({ email, user_id, otp_code, new_password }) => {
    const payload = { otp_code, new_password };
    if (email) payload.email = email;
    if (user_id) payload.user_id = user_id;
    const { data } = await axiosInstance.post("/auth/reset-password", payload);
    return data;
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ token: null, user: null, role: null, isAuthenticated: false });
  },

  completeProfile: async (payload) => {
    const { data } = await axiosInstance.post("/profile/complete", payload);
    set((state) => ({
      user: { ...state.user, ...data, userState: "ACTIVE" }
    }));
    return data;
  },

  updateProfile: async (payload) => {
    const { data } = await axiosInstance.post("/profile/update", payload);
    set((state) => ({
      user: { ...state.user, ...data }
    }));
    return data;
  },
}));
