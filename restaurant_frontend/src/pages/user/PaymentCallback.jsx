import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axiosInstance from "../../api/axiosInstance";
import { useCartStore } from "../../stores/cartStore";

export default function PaymentCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const clearCart = useCartStore((state) => state.clearCart);
  const hasRun = useRef(false);

  const urlStatus = searchParams.get("status");
  const transactionId = searchParams.get("transaction_id");
  const txRef = searchParams.get("tx_ref");
  const orderIdFromUrl = searchParams.get("order_id");

  const [phase, setPhase] = useState("verifying");

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const redirectToOrders = (paymentState, resolvedOrderId) => {
      const params = new URLSearchParams();
      if (paymentState) params.set("payment", paymentState);
      if (resolvedOrderId) params.set("orderId", resolvedOrderId);
      if (txRef) params.set("tx_ref", txRef);
      navigate(`/user/orders?${params.toString()}`, { replace: true });
    };

    async function verify() {
      if (urlStatus === "cancelled") {
        setPhase("pending");
        redirectToOrders("pending", orderIdFromUrl);
        return;
      }

      if (urlStatus === "failed") {
        setPhase("failed");
        redirectToOrders("failed", orderIdFromUrl);
        return;
      }

      if (!transactionId) {
        setPhase("pending");
        redirectToOrders("pending", orderIdFromUrl);
        return;
      }

      try {
        const { data } = await axiosInstance.get(`/payments/verify/${transactionId}`, {
          params: {
            tx_ref: txRef,
            order_id: orderIdFromUrl,
          },
        });

        if (data.paid) {
          clearCart();
          setPhase("paid");
          redirectToOrders("paid", data.order_id || orderIdFromUrl);
          return;
        }

        setPhase("pending");
        redirectToOrders("pending", data.order_id || orderIdFromUrl);
      } catch {
        setPhase("pending");
        redirectToOrders("pending", orderIdFromUrl);
      }
    }

    verify();
  }, [clearCart, navigate, orderIdFromUrl, transactionId, txRef, urlStatus]);

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4 font-body">
      <div className="w-full max-w-sm rounded-[2rem] bg-white p-10 text-center shadow-[0_8px_40px_rgba(0,0,0,0.06)] border border-gray-100 fade-up">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-brandCream">
          <svg className="animate-spin h-8 w-8 text-brandRed" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
        <h1 className="font-heading text-2xl font-extrabold text-gray-900 mb-2">
          {phase === "failed" ? "Payment Failed" : "Confirming Payment"}
        </h1>
        <p className="text-sm text-gray-500">
          Redirecting you to your orders page now.
        </p>
      </div>
    </main>
  );
}
