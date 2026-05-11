import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import { useCartStore } from "../../stores/cartStore";

const PAYMENT_METHOD = "banktransfer";

export default function Checkout() {
  const navigate = useNavigate();
  const items = useCartStore((state) => state.items);

  const total = items.reduce((acc, item) => acc + Number(item.price || 0) * item.quantity, 0);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState("");

  const handleCheckout = async () => {
    if (!items.length) return;

    try {
      setLoading(true);
      setError("");

      setLoadingStep("creating");
      const orderPayload = {
        items: items.map((item) => ({
          food_id: item.id || item.food_id,
          quantity: item.quantity,
        })),
      };
      const { data: order } = await axiosInstance.post("/orders", orderPayload);

      setLoadingStep("redirecting");
      const { data: paymentData } = await axiosInstance.post("/payments/initialize", {
        order_id: order.id,
        payment_options: PAYMENT_METHOD,
      });

      window.location.href = paymentData.payment_link;
    } catch (err) {
      setError(err.response?.data?.detail || "Could not start payment. Please try again.");
      setLoading(false);
      setLoadingStep("");
    }
  };

  const loadingLabel =
    loadingStep === "creating"
      ? "Creating order..."
      : loadingStep === "redirecting"
      ? "Redirecting to payment..."
      : "Processing...";

  return (
    <main className="page-wrapper bg-gray-50/50">
      <Navbar title="Secure Checkout" />

      <section className="mx-auto mt-4 w-full max-w-lg px-3 pb-28 sm:mt-6 sm:px-4 fade-up">
        <h1 className="mb-4 font-heading text-2xl font-extrabold text-gray-900 sm:mb-6 sm:text-3xl">Checkout</h1>

        {items.length === 0 ? (
          <div className="rounded-3xl bg-white p-6 text-center shadow-sm border border-gray-100 sm:p-8">
            <p className="text-gray-500 mb-4">Your cart is empty.</p>
            <button className="btn-primary w-full" onClick={() => navigate("/user/home")}>
              Go back to Menu
            </button>
          </div>
        ) : (
          <div className="space-y-4 sm:space-y-6">
            <div className="rounded-3xl bg-white p-4 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-gray-100 relative overflow-hidden sm:p-6">
              <div className="flex items-center justify-between gap-3 mb-4">
                <h2 className="font-heading text-lg font-bold text-gray-900 sm:text-xl">Order Summary</h2>
                <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-bold text-gray-600">
                  {items.length} item{items.length > 1 ? "s" : ""}
                </span>
              </div>
              <ul className="space-y-3 mb-6">
                {items.map((item, idx) => (
                  <li key={idx} className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-brandRed w-6">x{item.quantity}</span>
                      <span className="font-medium text-gray-700 truncate max-w-[180px]">{item.name}</span>
                    </div>
                    <span className="font-bold text-gray-900">
                      N{(Number(item.price) * item.quantity).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
              <div className="border-t border-dashed border-gray-200 pt-4 mt-4">
                <p className="text-sm font-semibold text-gray-500 mb-1">Total to Pay</p>
                <p className="font-heading text-2xl font-black text-brandRed sm:text-3xl">
                  N{total.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="rounded-3xl bg-white p-4 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-gray-100 sm:p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brandCream text-brandRed">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="5" width="20" height="14" rx="2" />
                    <line x1="2" y1="10" x2="22" y2="10" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-heading text-lg font-bold text-gray-900">Payment Method</h3>
                  <p className="text-xs font-medium text-gray-500">Continue to Flutterwave to complete payment</p>
                </div>
              </div>
              <button
                id="checkout-pay-btn"
                type="button"
                onClick={handleCheckout}
                disabled={loading}
                className="w-full rounded-2xl border-2 border-green-500 bg-green-50/50 p-4 text-left transition hover:bg-green-50 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-70"
              >
                <div className="flex items-center justify-center gap-3">
                  <div className="text-center">
                    <p className="text-sm font-bold text-green-700">
                      {loading ? loadingLabel : "Click here to make payment"}
                    </p>
                    <p className="text-xs font-medium text-green-700/80">
                      {loading
                        ? "Please wait while we prepare your secure checkout."
                        : `Pay N${total.toLocaleString()} securely with Flutterwave.`}
                    </p>
                  </div>
                </div>
              </button>
              <p className="text-center text-xs text-gray-400 mt-4 font-medium flex items-center justify-center gap-1">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                Secure payment via Flutterwave
              </p>
            </div>

            <div className="rounded-3xl bg-white p-4 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-gray-100 sm:p-6">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brandCream text-brandRed">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-heading text-lg font-bold text-gray-900">Delivery Details</h3>
                  <p className="text-xs font-medium text-gray-500">To be collected or standard delivery</p>
                </div>
              </div>
            </div>

            {error && (
              <div className="rounded-2xl bg-red-50 p-4 text-center text-sm font-semibold text-red-600 border border-red-100 animate-pulse">
                {error}
              </div>
            )}
          </div>
        )}
      </section>

      <BottomNav role="user" />
    </main>
  );
}
