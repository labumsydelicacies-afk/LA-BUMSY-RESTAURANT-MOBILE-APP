import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import { useCartStore } from "../../stores/cartStore";

export default function Checkout() {
  const navigate = useNavigate();
  const items = useCartStore((state) => state.items);
  const clearCart = useCartStore((state) => state.clearCart);
  
  const total = items.reduce((acc, item) => acc + Number(item.price || 0) * item.quantity, 0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCheckout = async () => {
    if (!items.length) return;
    try {
      setLoading(true);
      setError("");
      const payload = {
        items: items.map((item) => ({ food_id: item.id || item.food_id, quantity: item.quantity })),
      };
      await axiosInstance.post("/orders/", payload);
      clearCart();
      navigate("/user/orders");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not complete order. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-wrapper bg-gray-50/50">
      <Navbar title="Secure Checkout" />
      
      <section className="mx-4 mt-6 pb-28 max-w-lg mx-auto fade-up">
        <h1 className="font-heading text-3xl font-extrabold text-gray-900 mb-6">Checkout</h1>

        {items.length === 0 ? (
          <div className="rounded-[2rem] bg-white p-8 text-center shadow-sm border border-gray-100">
            <p className="text-gray-500 mb-4">Your cart is empty.</p>
            <button className="btn-primary w-full" onClick={() => navigate("/user/home")}>
              Go back to Menu
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Order Items Preview */}
            <div className="rounded-3xl bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-gray-100 relative overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-heading text-xl font-bold text-gray-900">Order Summary</h2>
                <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-bold text-gray-600">
                  {items.length} item{items.length > 1 ? 's' : ''}
                </span>
              </div>
              
              <ul className="space-y-3 mb-6">
                {items.map((item, idx) => (
                  <li key={idx} className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-brandRed w-6">x{item.quantity}</span>
                      <span className="font-medium text-gray-700 truncate max-w-[180px]">{item.name}</span>
                    </div>
                    <span className="font-bold text-gray-900">₦{(Number(item.price) * item.quantity).toLocaleString()}</span>
                  </li>
                ))}
              </ul>
              
              <div className="border-t border-dashed border-gray-200 pt-4 mt-4">
                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-sm font-semibold text-gray-500 mb-1">Total to Pay</p>
                    <p className="font-heading text-3xl font-black text-brandRed">
                      ₦{total.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Delivery/Payment Info Placeholder */}
            <div className="rounded-3xl bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-gray-100">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brandCream text-brandRed">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                </div>
                <div>
                  <h3 className="font-heading text-lg font-bold text-gray-900">Delivery Details</h3>
                  <p className="text-xs font-medium text-gray-500">To be collected or standard delivery</p>
                </div>
              </div>
            </div>

            {error ? (
              <div className="rounded-2xl bg-red-50 p-4 text-center text-sm font-semibold text-red-600 border border-red-100 animate-pulse">
                {error}
              </div>
            ) : null}

            <div className="pt-4">
              <button
                className="btn-primary w-full py-4 text-lg shadow-[0_8px_25px_rgba(232,34,10,0.25)] relative overflow-hidden group disabled:opacity-60 disabled:shadow-none"
                onClick={handleCheckout}
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Processing...
                  </span>
                ) : (
                  <>
                    Confirm Order
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="absolute right-6 transition-transform duration-300 group-hover:translate-x-1"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                  </>
                )}
              </button>
              <p className="text-center text-xs text-gray-400 mt-4 font-medium flex items-center justify-center gap-1">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                Secure 256-bit encrypted checkout
              </p>
            </div>
          </div>
        )}
      </section>
      
      <BottomNav role="user" />
    </main>
  );
}
