import { useEffect, useRef, useState } from "react";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import OrderCard from "../../components/OrderCard";
import { useSocketStore } from "../../stores/socketStore";

// ─── Spinner ────────────────────────────────────────────────────────────────
function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 text-white"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

// ─── OTP Input (6-box) ───────────────────────────────────────────────────────
function OtpInput({ value, onChange }) {
  const OTP_LENGTH = 6;
  const handleBox = (index, raw) => {
    const digit = raw.replace(/\D/g, "").slice(-1);
    const chars = value.split("");
    chars[index] = digit;
    const next = chars.join("").slice(0, OTP_LENGTH);
    onChange(next);
    if (digit && index < OTP_LENGTH - 1) {
      document.getElementById(`delivery-otp-${index + 1}`)?.focus();
    }
  };
  const handleKey = (index, e) => {
    if (e.key === "Backspace" && !value[index] && index > 0) {
      document.getElementById(`delivery-otp-${index - 1}`)?.focus();
    }
  };
  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, OTP_LENGTH);
    if (pasted) { e.preventDefault(); onChange(pasted); }
  };
  return (
    <div className="flex items-center justify-between gap-2" onPaste={handlePaste}>
      {Array.from({ length: OTP_LENGTH }).map((_, i) => (
        <input
          key={i}
          id={`delivery-otp-${i}`}
          type="text"
          inputMode="numeric"
          maxLength={1}
          className="h-11 w-10 box-border rounded-xl border border-gray-200 text-center text-lg font-semibold outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
          value={value[i] || ""}
          onChange={(e) => handleBox(i, e.target.value)}
          onKeyDown={(e) => handleKey(i, e)}
        />
      ))}
    </div>
  );
}

// ─── Main Dashboard ──────────────────────────────────────────────────────────
export default function RiderDashboard() {
  const [available, setAvailable] = useState([]);
  const [myDeliveries, setMyDeliveries] = useState([]);
  const [loadingAvail, setLoadingAvail] = useState(true);
  const [loadingMine, setLoadingMine] = useState(true);
  const [accepting, setAccepting] = useState(null);
  const [pickingUp, setPickingUp] = useState(null);
  const [completing, setCompleting] = useState(null);
  const [otpValues, setOtpValues] = useState({});   // keyed by order_id
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const connect = useSocketStore((s) => s.connect);
  const disconnect = useSocketStore((s) => s.disconnect);
  const successTimer = useRef(null);

  const flash = (msg) => {
    setSuccessMsg(msg);
    clearTimeout(successTimer.current);
    successTimer.current = setTimeout(() => setSuccessMsg(""), 4000);
  };

  // ── fetch available orders (ready_for_pickup, no rider) ──────────────────
  const fetchAvailable = async () => {
    try {
      const { data } = await axiosInstance.get("/delivery/available");
      setAvailable(Array.isArray(data) ? data : []);
      setError("");
    } catch (err) {
      setAvailable([]);
      setError(err.response?.data?.detail || "Could not load available orders.");
    } finally {
      setLoadingAvail(false);
    }
  };

  // ── fetch my assigned deliveries ─────────────────────────────────────────
  const fetchMine = async () => {
    try {
      const { data } = await axiosInstance.get("/delivery/my-deliveries");
      setMyDeliveries(Array.isArray(data) ? data : []);
    } catch {
      setMyDeliveries([]);
    } finally {
      setLoadingMine(false);
    }
  };

  useEffect(() => {
    fetchAvailable();
    fetchMine();
    connect({ onOrderStatusChanged: () => { fetchAvailable(); fetchMine(); } });
    return () => { disconnect(); clearTimeout(successTimer.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── accept ────────────────────────────────────────────────────────────────
  const handleAccept = async (orderId) => {
    try {
      setAccepting(orderId);
      setError("");
      await axiosInstance.post("/delivery/accept", { order_id: orderId });
      flash("Order accepted! Head to the restaurant to pick it up.");
      await Promise.all([fetchAvailable(), fetchMine()]);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not accept order.");
    } finally {
      setAccepting(null);
    }
  };

  // ── picked up ─────────────────────────────────────────────────────────────
  const handlePickup = async (orderId) => {
    try {
      setPickingUp(orderId);
      setError("");
      await axiosInstance.patch(`/delivery/pickup/${orderId}`);
      flash("Picked up! The customer has been sent their delivery code.");
      await fetchMine();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not mark as picked up.");
    } finally {
      setPickingUp(null);
    }
  };

  // ── complete delivery (OTP) ───────────────────────────────────────────────
  const handleComplete = async (orderId) => {
    const otp = (otpValues[orderId] || "").trim();
    if (otp.length < 6) { setError("Enter the full 6-digit code from the customer."); return; }
    try {
      setCompleting(orderId);
      setError("");
      await axiosInstance.post("/delivery/complete", { order_id: orderId, otp });
      flash("Delivery confirmed! Great job.");
      setOtpValues((prev) => { const n = { ...prev }; delete n[orderId]; return n; });
      await fetchMine();
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired code.");
    } finally {
      setCompleting(null);
    }
  };

  // ── derive active (picked-up but not delivered) for OTP entry ────────────
  const activeDeliveries = myDeliveries.filter((d) => d.picked_up_at && !d.delivered_at);
  const pendingDeliveries = myDeliveries.filter((d) => !d.picked_up_at);
  const completedDeliveries = myDeliveries.filter((d) => d.delivered_at);

  return (
    <main>
      <Navbar title="Rider dashboard" />
      <section className="space-y-6 px-4 pb-24 pt-2">

        {/* Global feedback */}
        {error ? (
          <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-brandRed border border-rose-100">
            {error}
          </p>
        ) : null}
        {successMsg ? (
          <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 border border-emerald-100">
            {successMsg}
          </p>
        ) : null}

        {/* ── SECTION 1: Available Orders ─────────────────────────────── */}
        <div>
          <h2 className="mb-3 font-heading text-base font-bold text-gray-800 uppercase tracking-wide">
            Available Orders
          </h2>
          {loadingAvail ? (
            <p className="text-sm text-gray-500">Loading...</p>
          ) : available.length === 0 ? (
            <p className="text-sm text-gray-400">No orders ready for pickup right now.</p>
          ) : (
            <div className="space-y-3">
              {available.map((order) => (
                <OrderCard key={order.id} order={order}>
                  <button
                    id={`accept-order-${order.id}`}
                    className="w-full rounded-xl bg-brandRed py-2.5 text-sm font-semibold text-white transition hover:bg-red-700 disabled:opacity-60 flex items-center justify-center gap-2"
                    onClick={() => handleAccept(order.id)}
                    disabled={accepting === order.id}
                  >
                    {accepting === order.id ? <><Spinner /> Accepting...</> : "Accept Order"}
                  </button>
                </OrderCard>
              ))}
            </div>
          )}
        </div>

        {/* ── SECTION 2: My Active Deliveries (accepted, not yet picked up) */}
        {pendingDeliveries.length > 0 ? (
          <div>
            <h2 className="mb-3 font-heading text-base font-bold text-gray-800 uppercase tracking-wide">
              Head to Restaurant
            </h2>
            <div className="space-y-3">
              {pendingDeliveries.map((delivery) => (
                <div
                  key={delivery.id}
                  className="rounded-3xl bg-white p-5 border border-gray-100 shadow-[0_8px_24px_rgba(0,0,0,0.04)]"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <p className="font-heading text-lg font-black text-gray-900">
                      Order #{String(delivery.order_id).slice(-6)}
                    </p>
                    <span className="rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wider bg-indigo-100 text-indigo-800 border-indigo-200">
                      Accepted
                    </span>
                  </div>
                  <p className="mb-4 text-sm text-gray-500">
                    Accepted {new Date(delivery.assigned_at).toLocaleString("en-US", {
                      month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
                    })}
                  </p>
                  <button
                    id={`pickup-order-${delivery.order_id}`}
                    className="w-full rounded-xl bg-brandYellow py-2.5 text-sm font-semibold text-gray-900 transition hover:brightness-95 disabled:opacity-60 flex items-center justify-center gap-2"
                    onClick={() => handlePickup(delivery.order_id)}
                    disabled={pickingUp === delivery.order_id}
                  >
                    {pickingUp === delivery.order_id ? <><Spinner /> Updating...</> : "I've Picked It Up"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* ── SECTION 3: Out for Delivery — OTP entry ─────────────────── */}
        {activeDeliveries.length > 0 ? (
          <div>
            <h2 className="mb-3 font-heading text-base font-bold text-gray-800 uppercase tracking-wide">
              Confirm Delivery
            </h2>
            <p className="mb-3 text-xs text-gray-500">
              Ask the customer for their code and enter it below to complete the delivery.
            </p>
            <div className="space-y-3">
              {activeDeliveries.map((delivery) => (
                <div
                  key={delivery.id}
                  className="rounded-3xl bg-white p-5 border border-gray-100 shadow-[0_8px_24px_rgba(0,0,0,0.04)]"
                >
                  <div className="mb-4 flex items-center justify-between">
                    <p className="font-heading text-lg font-black text-gray-900">
                      Order #{String(delivery.order_id).slice(-6)}
                    </p>
                    <span className="rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wider bg-cyan-100 text-cyan-800 border-cyan-200">
                      On the Way
                    </span>
                  </div>
                  <OtpInput
                    value={otpValues[delivery.order_id] || ""}
                    onChange={(v) =>
                      setOtpValues((prev) => ({ ...prev, [delivery.order_id]: v }))
                    }
                  />
                  <button
                    id={`complete-delivery-${delivery.order_id}`}
                    className="mt-4 w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60 flex items-center justify-center gap-2"
                    onClick={() => handleComplete(delivery.order_id)}
                    disabled={
                      completing === delivery.order_id ||
                      (otpValues[delivery.order_id] || "").length < 6
                    }
                  >
                    {completing === delivery.order_id ? (
                      <><Spinner /> Verifying...</>
                    ) : (
                      "Confirm Delivery"
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* ── SECTION 4: Completed deliveries ─────────────────────────── */}
        {completedDeliveries.length > 0 ? (
          <div>
            <h2 className="mb-3 font-heading text-base font-bold text-gray-800 uppercase tracking-wide">
              Completed
            </h2>
            <div className="space-y-3">
              {completedDeliveries.map((delivery) => (
                <div
                  key={delivery.id}
                  className="rounded-3xl bg-white p-5 border border-gray-100 shadow-[0_8px_24px_rgba(0,0,0,0.04)]"
                >
                  <div className="flex items-center justify-between">
                    <p className="font-heading text-base font-black text-gray-900">
                      Order #{String(delivery.order_id).slice(-6)}
                    </p>
                    <span className="rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border-emerald-200">
                      Delivered
                    </span>
                  </div>
                  {delivery.delivered_at ? (
                    <p className="mt-1 text-xs text-gray-400">
                      {new Date(delivery.delivered_at).toLocaleString("en-US", {
                        month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
                      })}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* Empty state */}
        {!loadingAvail && !loadingMine &&
          available.length === 0 &&
          myDeliveries.length === 0 ? (
          <p className="py-8 text-center text-sm text-gray-400">
            No active deliveries. Check back soon.
          </p>
        ) : null}

      </section>
      <BottomNav role="rider" />
    </main>
  );
}
