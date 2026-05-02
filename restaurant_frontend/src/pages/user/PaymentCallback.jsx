import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axiosInstance from "../../api/axiosInstance";
import { useCartStore } from "../../stores/cartStore";

/*
 * PaymentCallback
 * ───────────────
 * Flutterwave redirects the user here after they attempt payment, whether
 * successful, failed, or abandoned. Query params from Flutterwave:
 *
 *   ?status=successful&tx_ref=order_42_1234567890&transaction_id=123456789
 *   ?status=cancelled&tx_ref=...
 *   ?status=failed&tx_ref=...
 *
 * This page:
 *   1. Reads the status and transaction_id from the URL.
 *   2. If status is "successful": calls GET /payments/verify/{transaction_id}
 *      to do a server-side confirmation (backend is the source of truth).
 *   3. On confirmed: clears the cart and shows a success screen.
 *   4. On pending/failed/cancelled: shows appropriate messaging with retry
 *      or back-to-orders options.
 *
 * IMPORTANT: We never mark an order paid based on the URL status alone.
 * The verify endpoint does the real check against Flutterwave's API.
 */
export default function PaymentCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const clearCart = useCartStore((state) => state.clearCart);

  const urlStatus      = searchParams.get("status");        // "successful" | "cancelled" | "failed"
  const transactionId  = searchParams.get("transaction_id"); // Flutterwave numeric tx ID
  const txRef          = searchParams.get("tx_ref");         // our order_{id}_{ts} ref

  const [phase, setPhase] = useState("verifying"); // "verifying" | "paid" | "pending" | "failed"
  const [orderId, setOrderId] = useState(null);
  const hasRun = useRef(false);

  useEffect(() => {
    // Strict-mode double-fire guard
    if (hasRun.current) return;
    hasRun.current = true;

    async function verify() {
      // ── Abandoned / explicitly cancelled by user ──────────────────────
      if (urlStatus === "cancelled") {
        setPhase("pending");
        return;
      }

      // ── Flutterwave reported failure upfront ──────────────────────────
      if (urlStatus === "failed") {
        setPhase("failed");
        return;
      }

      // ── status === "successful" — verify server-side ──────────────────
      if (!transactionId) {
        // No transaction_id means we can't verify — treat as pending.
        setPhase("pending");
        return;
      }

      try {
        const { data } = await axiosInstance.get(
          `/payments/verify/${transactionId}`
        );

        if (data.paid) {
          clearCart();
          setOrderId(data.order_id);
          setPhase("paid");
        } else {
          setPhase("pending");
        }
      } catch {
        // Network error or 404 — don't assume failure, show pending
        setPhase("pending");
      }
    }

    verify();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4 font-body">
      <div className="w-full max-w-sm">

        {/* ── VERIFYING ─────────────────────────────────────────── */}
        {phase === "verifying" && (
          <div className="rounded-[2rem] bg-white p-10 text-center shadow-[0_8px_40px_rgba(0,0,0,0.06)] border border-gray-100 fade-up">
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-brandCream">
              <svg className="animate-spin h-8 w-8 text-brandRed" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <h1 className="font-heading text-2xl font-extrabold text-gray-900 mb-2">
              Confirming Payment
            </h1>
            <p className="text-sm text-gray-500">
              Please wait while we verify your payment with Flutterwave…
            </p>
          </div>
        )}

        {/* ── PAID ──────────────────────────────────────────────── */}
        {phase === "paid" && (
          <div className="rounded-[2rem] bg-white p-10 text-center shadow-[0_8px_40px_rgba(0,0,0,0.06)] border border-gray-100 fade-up">
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-50 text-5xl">
              ✅
            </div>
            <h1 className="font-heading text-2xl font-extrabold text-gray-900 mb-2">
              Payment Confirmed!
            </h1>
            <p className="text-sm text-gray-500 mb-1">
              Your order has been received and is being prepared.
            </p>
            {orderId && (
              <p className="text-xs text-gray-400 mb-6">Order #{orderId}</p>
            )}
            <button
              id="payment-success-view-orders"
              className="btn-primary w-full py-3"
              onClick={() => navigate("/user/orders")}
            >
              View My Orders
            </button>
          </div>
        )}

        {/* ── PENDING / ABANDONED ───────────────────────────────── */}
        {phase === "pending" && (
          <div className="rounded-[2rem] bg-white p-10 text-center shadow-[0_8px_40px_rgba(0,0,0,0.06)] border border-gray-100 fade-up">
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-yellow-50 text-5xl">
              ⏳
            </div>
            <h1 className="font-heading text-2xl font-extrabold text-gray-900 mb-2">
              Payment Pending
            </h1>
            <p className="text-sm text-gray-500 mb-6">
              We haven't received payment confirmation yet. If you completed the
              transfer, it may take a few minutes. Your order is saved — check
              back shortly.
            </p>
            <div className="space-y-3">
              <button
                id="payment-pending-view-orders"
                className="btn-primary w-full py-3"
                onClick={() => navigate("/user/orders")}
              >
                Check My Orders
              </button>
              <button
                className="w-full py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 transition-colors"
                onClick={() => navigate("/user/home")}
              >
                Back to Menu
              </button>
            </div>
          </div>
        )}

        {/* ── FAILED ────────────────────────────────────────────── */}
        {phase === "failed" && (
          <div className="rounded-[2rem] bg-white p-10 text-center shadow-[0_8px_40px_rgba(0,0,0,0.06)] border border-gray-100 fade-up">
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-50 text-5xl">
              ❌
            </div>
            <h1 className="font-heading text-2xl font-extrabold text-gray-900 mb-2">
              Payment Failed
            </h1>
            <p className="text-sm text-gray-500 mb-6">
              Your payment was not completed. No money has been deducted. You can
              try again from your orders page.
            </p>
            <div className="space-y-3">
              <button
                id="payment-failed-try-again"
                className="btn-primary w-full py-3"
                onClick={() => navigate("/user/orders")}
              >
                Try Again from Orders
              </button>
              <button
                className="w-full py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 transition-colors"
                onClick={() => navigate("/user/home")}
              >
                Back to Menu
              </button>
            </div>
          </div>
        )}

        {/* Tx reference for support */}
        {txRef && phase !== "verifying" && (
          <p className="text-center text-xs text-gray-300 mt-4">
            Ref: {txRef}
          </p>
        )}
      </div>
    </main>
  );
}
