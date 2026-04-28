import { create } from "zustand";

export const useCartStore = create((set, get) => ({
  items: [],
  addToCart: (food, quantity = 1) =>
    set((state) => {
      const existing = state.items.find((item) => item.id === food.id);
      window.dispatchEvent(new CustomEvent("app:toast", { detail: { message: `Added ${food.name} to cart` } }));
      if (existing) {
        return {
          items: state.items.map((item) =>
            item.id === food.id ? { ...item, quantity: item.quantity + quantity } : item
          ),
        };
      }
      return {
        items: [...state.items, { ...food, quantity }],
      };
    }),
  removeFromCart: (foodId) =>
    set((state) => ({
      items: state.items
        .map((item) =>
          item.id === foodId ? { ...item, quantity: item.quantity - 1 } : item
        )
        .filter((item) => item.quantity > 0),
    })),
  clearCart: () => set({ items: [] }),
  getTotal: () =>
    get().items.reduce((acc, item) => acc + Number(item.price || 0) * item.quantity, 0),
}));
