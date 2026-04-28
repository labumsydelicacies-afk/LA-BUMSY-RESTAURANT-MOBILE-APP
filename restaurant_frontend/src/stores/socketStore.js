import { io } from "socket.io-client";
import { create } from "zustand";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const useSocketStore = create((set, get) => ({
  socket: null,
  connected: false,
  pollingTimer: null,

  connect: ({ onFoodUpdated, onOrderStatusChanged }) => {
    if (get().socket) return;

    const token = localStorage.getItem("token");
    const socket = io(API_BASE_URL, {
      transports: ["websocket", "polling"],
      auth: token ? { token } : undefined,
    });

    socket.on("connect", () => {
      set({ connected: true });
      if (get().pollingTimer) {
        clearInterval(get().pollingTimer);
        set({ pollingTimer: null });
      }
    });

    socket.on("disconnect", () => set({ connected: false }));
    socket.on("food_updated", () => onFoodUpdated?.());
    socket.on("order_status_changed", (payload) => onOrderStatusChanged?.(payload));

    socket.on("connect_error", () => {
      if (!get().pollingTimer) {
        const timer = setInterval(() => {
          onFoodUpdated?.();
          onOrderStatusChanged?.();
        }, 10000);
        set({ pollingTimer: timer });
      }
    });

    set({ socket });
  },

  disconnect: () => {
    const { socket, pollingTimer } = get();
    if (pollingTimer) clearInterval(pollingTimer);
    if (socket) socket.disconnect();
    set({ socket: null, connected: false, pollingTimer: null });
  },
}));
