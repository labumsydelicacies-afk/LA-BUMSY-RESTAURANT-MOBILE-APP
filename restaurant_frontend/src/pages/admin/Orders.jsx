import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import OrderCard from "../../components/OrderCard";
import { useSocketStore } from "../../stores/socketStore";

const statuses = ["pending", "confirmed", "preparing", "ready_for_pickup", "out_for_delivery", "delivered", "cancelled"];

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
      <section className="space-y-3 px-4 pb-24 pt-2">
        {loading ? <p className="text-sm text-gray-500">Loading orders...</p> : null}
        {error ? <p className="text-sm text-brandRed">{error}</p> : null}
        {orders.map((order) => (
          <OrderCard key={order.id} order={order}>
            <select
              className="w-full rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
              value={order.status}
              onChange={(e) => handleStatusUpdate(order.id, e.target.value)}
              disabled={updatingStatus === order.id}
            >
              {statuses.map((status) => (
                <option value={status} key={status}>
                  {status}
                </option>
              ))}
            </select>
          </OrderCard>
        ))}
      </section>
      <BottomNav role="admin" />
    </main>
  );
}
