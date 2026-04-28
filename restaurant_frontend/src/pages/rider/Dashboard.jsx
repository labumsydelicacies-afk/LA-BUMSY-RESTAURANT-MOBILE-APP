import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import OrderCard from "../../components/OrderCard";
import { useSocketStore } from "../../stores/socketStore";

export default function Dashboard() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(null);
  const [error, setError] = useState("");
  const connect = useSocketStore((state) => state.connect);
  const disconnect = useSocketStore((state) => state.disconnect);

  const fetchOrders = async () => {
    try {
      const { data } = await axiosInstance.get("/orders/");
      const normalized = Array.isArray(data) ? data : data.orders || [];
      setOrders(
        normalized.filter((order) =>
          ["confirmed", "preparing"].includes(order.status)
        )
      );
      setError("");
    } catch (err) {
      setOrders([]);
      if (err.response?.status === 404) {
        setError("Orders endpoint is not available yet.");
      } else {
        setError(err.response?.data?.detail || "Could not load delivery orders.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    connect({ onOrderStatusChanged: fetchOrders });
    return () => disconnect();
  }, []);

  const updateStatus = async (orderId, status) => {
    try {
      setUpdating(orderId);
      setError("");
      await axiosInstance.patch(`/orders/${orderId}/status`, { status });
      setOrders((prev) => prev.filter((order) => order.id !== orderId));
    } catch (err) {
      if (err.response?.status === 404) {
        setError("Order status update endpoint is not available yet.");
      } else {
        setError(err.response?.data?.detail || "Could not update delivery status.");
      }
    } finally {
      setUpdating(null);
    }
  };

  return (
    <main>
      <Navbar title="Rider dashboard" />
      <section className="space-y-3 px-4 pb-24 pt-2">
        {error ? <p className="text-sm text-brandRed">{error}</p> : null}
        {loading ? (
          <p className="text-sm text-gray-500">Loading orders...</p>
        ) : (
          orders.map((order) => (
            <OrderCard key={order.id} order={order}>
              <div className="grid grid-cols-2 gap-2">
                <button
                  className="rounded-lg bg-brandYellow px-3 py-2 text-xs font-semibold disabled:opacity-50"
                  onClick={() => updateStatus(order.id, "preparing")}
                  disabled={updating === order.id}
                >
                  {updating === order.id ? "Updating..." : "Preparing"}
                </button>
                <button
                  className="rounded-lg bg-brandRed px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
                  onClick={() => updateStatus(order.id, "delivered")}
                  disabled={updating === order.id}
                >
                  {updating === order.id ? "Updating..." : "Delivered"}
                </button>
              </div>
            </OrderCard>
          ))
        )}
        {!loading && orders.length === 0 ? <p className="text-sm text-gray-500">No active delivery orders.</p> : null}
      </section>
      <BottomNav role="rider" />
    </main>
  );
}
