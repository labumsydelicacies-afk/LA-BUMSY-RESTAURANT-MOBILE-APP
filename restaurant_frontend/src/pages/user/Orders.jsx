import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import OrderCard from "../../components/OrderCard";
import { useAuthStore } from "../../stores/authStore";
import { useSocketStore } from "../../stores/socketStore";
import { Link } from "react-router-dom";

export default function Orders() {
  const user = useAuthStore((state) => state.user);
  const connect = useSocketStore((state) => state.connect);
  const disconnect = useSocketStore((state) => state.disconnect);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchOrders = async () => {
    try {
      const { data } = await axiosInstance.get("/orders/");
      const normalized = Array.isArray(data) ? data : data.orders || [];
      const userId = Number(user?.id);
      // Support backend returning either list of orders or { orders: [...] } and mixed id types.
      setOrders(
        normalized
          .filter((order) => Number(order.user_id) === userId)
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      );
      setError("");
    } catch (err) {
      setOrders([]);
      if (err.response?.status === 404) {
        setError("Order history is currently unavailable.");
      } else {
        setError(err.response?.data?.detail || "Could not load your orders.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    connect({ onOrderStatusChanged: fetchOrders });
    return () => disconnect();
  }, [user?.id, connect, disconnect]);

  return (
    <main className="page-wrapper bg-gray-50/50">
      <Navbar title="Your Order History" />
      
      <section className="mx-4 mt-6 pb-28 max-w-lg mx-auto">
        <h1 className="font-heading text-3xl font-extrabold text-gray-900 mb-6 fade-up">My Orders</h1>

        {loading ? (
          <div className="space-y-4 fade-up" style={{ animationDelay: '0.1s' }}>
            {[...Array(3)].map((_, i) => (
              <div key={i} className="rounded-3xl bg-white p-5 shadow-[0_4px_20px_rgba(0,0,0,0.02)] border border-gray-100 animate-pulse">
                <div className="flex items-center justify-between mb-4">
                  <div className="h-5 w-24 rounded bg-gray-200" />
                  <div className="h-6 w-20 rounded-full bg-gray-200" />
                </div>
                <div className="h-4 w-1/3 rounded bg-gray-200 mb-6" />
                <div className="flex justify-between items-center pt-4 border-t border-gray-100">
                  <div className="h-4 w-1/4 rounded bg-gray-200" />
                  <div className="h-6 w-1/4 rounded bg-gray-200" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="rounded-2xl bg-red-50 p-6 text-center text-red-600 border border-red-100 fade-up">
            <span className="text-3xl block mb-2">⚠️</span>
            <p className="font-semibold">{error}</p>
          </div>
        ) : orders.length > 0 ? (
          <div className="space-y-4">
            {orders.map((order, idx) => (
              <div key={order.id} className="fade-up" style={{ animationDelay: `${0.1 + (idx * 0.05)}s` }}>
                <OrderCard order={order} />
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-[2rem] bg-white p-12 text-center shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 fade-up" style={{ animationDelay: '0.1s' }}>
            <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-brandCream text-5xl">
              🧾
            </div>
            <p className="font-heading text-xl font-bold text-gray-800 mb-2">No orders yet</p>
            <p className="text-sm text-gray-500 mb-8">When you place an order, it will appear here so you can track its status.</p>
            <Link to="/user/home" className="btn-primary w-full shadow-md">
              Start Ordering
            </Link>
          </div>
        )}
      </section>
      
      <BottomNav role="user" />
    </main>
  );
}
