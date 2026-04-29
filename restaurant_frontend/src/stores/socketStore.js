import { create } from "zustand";

export const useSocketStore = create((set, get) => ({
  socket: null,
  connected: false,
  pollingTimer: null,

  connect: ({ onFoodUpdated, onOrderStatusChanged }) => {
    if (get().pollingTimer) return;

    const timer = setInterval(() => {
      onFoodUpdated?.();
      onOrderStatusChanged?.();
    }, 10000);

    set({ connected: false, pollingTimer: timer });
  },

  disconnect: () => {
    const { pollingTimer } = get();
    if (pollingTimer) clearInterval(pollingTimer);
    set({ socket: null, connected: false, pollingTimer: null });
  },
}));
