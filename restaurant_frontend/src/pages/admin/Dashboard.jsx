import { useEffect, useMemo, useState } from "react";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import { useSocketStore } from "../../stores/socketStore";

export default function Dashboard() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
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
        setError(err.response?.data?.detail || "Could not load dashboard stats.");
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

  const stats = useMemo(() => {
    const totalRevenue = orders.reduce((sum, order) => sum + Number(order.total_price || 0), 0);
    return {
      totalOrders: orders.length,
      delivered: orders.filter((order) => order.status === "delivered").length,
      pending: orders.filter((order) => order.status === "pending").length,
      revenue: totalRevenue,
    };
  }, [orders]);

  return (
    <main>
      <Navbar title="Admin dashboard" />
      <section className="grid grid-cols-2 gap-3 px-4 pb-24 pt-2">
        {error ? <p className="col-span-2 text-sm text-brandRed">{error}</p> : null}
        {loading ? (
          <div className="col-span-2 space-y-3">
            <div className="rounded-xl bg-white p-4 shadow-card animate-pulse">
              <p className="text-xs text-gray-500">Total Orders</p>
              <p className="font-heading text-2xl font-bold">--</p>
            </div>
            <div className="rounded-xl bg-white p-4 shadow-card animate-pulse">
              <p className="text-xs text-gray-500">Revenue</p>
              <p className="font-heading text-2xl font-bold text-brandRed">N--</p>
            </div>
            <div className="rounded-xl bg-white p-4 shadow-card animate-pulse">
              <p className="text-xs text-gray-500">Delivered</p>
              <p className="font-heading text-2xl font-bold">--</p>
            </div>
            <div className="rounded-xl bg-white p-4 shadow-card animate-pulse">
              <p className="text-xs text-gray-500">Pending</p>
              <p className="font-heading text-2xl font-bold">--</p>
            </div>
          </div>
        ) : (
          <>
            <div className="rounded-xl bg-white p-4 shadow-card">
              <p className="text-xs text-gray-500">Total Orders</p>
              <p className="font-heading text-2xl font-bold">{stats.totalOrders}</p>
            </div>
            <div className="rounded-xl bg-white p-4 shadow-card">
              <p className="text-xs text-gray-500">Revenue</p>
              <p className="font-heading text-2xl font-bold text-brandRed">N{stats.revenue.toLocaleString()}</p>
            </div>
            <div className="rounded-xl bg-white p-4 shadow-card">
              <p className="text-xs text-gray-500">Delivered</p>
              <p className="font-heading text-2xl font-bold">{stats.delivered}</p>
            </div>
            <div className="rounded-xl bg-white p-4 shadow-card">
              <p className="text-xs text-gray-500">Pending</p>
              <p className="font-heading text-2xl font-bold">{stats.pending}</p>
            </div>
          </>
        )}
      </section>
      <BottomNav role="admin" />
    </main>
  );
}
