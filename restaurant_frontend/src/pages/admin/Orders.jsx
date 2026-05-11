import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import OrderCard from "../../components/OrderCard";
import { useSocketStore } from "../../stores/socketStore";

const statuses = ["pending", "confirmed", "preparing", "ready_for_pickup", "out_for_delivery", "delivered", "cancelled"];
const riderTriggerStatuses = new Set(["ready_for_pickup", "out_for_delivery", "delivered"]);

function getAllowedStatuses(order) {
  const currentStatus = String(order.status || "").toLowerCase();
  const riderAccepted = Boolean(order.rider_id);
  return statuses.filter((statusOption) => {
    if (statusOption !== "out_for_delivery") return true;
    // Admin can only set this after rider accepts (rider_id assigned)
    // unless already out_for_delivery/delivered/cancelled.
    if (riderAccepted) return true;
    return currentStatus === "out_for_delivery";
  });
}

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [updatingStatus, setUpdatingStatus] = useState(null);
  const connect = useSocketStore((state) => state.connect);
  const disconnect = useSocketStore((state) => state.disconnect);

  const fetchOrders = async () => {
    try {
      const { data } = await axiosInstance.get("/orders");
      setOrders(Array.isArray(data) ? data : data.orders || []);
      setError("");
    } catch (err) {
      setOrders([]);
      if (err.response?.status === 404) {
        setError("Orders endpoint is not available yet.");
      } else {
        setError(err.response?.data?.detail || "Could not load orders.");
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

  const handleStatusUpdate = async (orderId, newStatus) => {
    try {
      setUpdatingStatus(orderId);
      setError("");
      await axiosInstance.patch(`/orders/${orderId}/status`, { status: newStatus });
      await fetchOrders();
    } catch (err) {
      if (err.response?.status === 404) {
        setError("Order status update endpoint is not available yet.");
      } else {
        setError(err.response?.data?.detail || "Could not update order status.");
      }
    } finally {
      setUpdatingStatus(null);
    }
  };

  return (
    <main>
      <Navbar title="All orders" />
      <section className="mx-auto w-full max-w-lg space-y-3 px-3 pb-24 pt-3 sm:px-4">
        {loading ? <p className="text-sm text-gray-500">Loading orders...</p> : null}
        {error ? <p className="text-sm text-brandRed">{error}</p> : null}
        {orders.map((order, index) => (
          <div
            key={order.id}
            className="slide-up"
            style={{ animationDelay: `${index * 55}ms` }}
          >
            <OrderCard order={order} showDeliveryOtp={false}>
              {riderTriggerStatuses.has(String(order.status || "").toLowerCase()) ? (
                <p className="mb-2 text-xs font-medium text-gray-600">
                  {order.rider_id
                    ? `Rider accepted: ${order.rider_name || `Rider #${order.rider_id}`}`
                    : "Awaiting rider acceptance"}
                </p>
              ) : null}
              <select
                className="w-full rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
                value={order.status}
                onChange={(e) => handleStatusUpdate(order.id, e.target.value)}
                disabled={updatingStatus === order.id}
              >
                {getAllowedStatuses(order).map((status) => (
                  <option value={status} key={status}>
                    {status}
                  </option>
                ))}
              </select>
            </OrderCard>
          </div>
        ))}
      </section>
      <BottomNav role="admin" />
    </main>
  );
}
