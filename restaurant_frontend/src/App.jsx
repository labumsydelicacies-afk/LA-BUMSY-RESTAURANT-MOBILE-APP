import { Navigate, Route, Routes } from "react-router-dom";
import { Suspense, lazy, useEffect, useState } from "react";
import ProtectedRoute from "./routes/ProtectedRoute";
import { useAuthStore } from "./stores/authStore";

const Login = lazy(() => import("./pages/auth/Login"));
const Register = lazy(() => import("./pages/auth/Register"));
const Home = lazy(() => import("./pages/user/Home"));
const FoodDetail = lazy(() => import("./pages/user/FoodDetail"));
const Cart = lazy(() => import("./pages/user/Cart"));
const Checkout = lazy(() => import("./pages/user/Checkout"));
const UserOrders = lazy(() => import("./pages/user/Orders"));
const AdminDashboard = lazy(() => import("./pages/admin/Dashboard"));
const AdminMenu = lazy(() => import("./pages/admin/Menu"));
const AdminOrders = lazy(() => import("./pages/admin/Orders"));
const AdminUsers = lazy(() => import("./pages/admin/Users"));
const RiderDashboard = lazy(() => import("./pages/rider/Dashboard"));

function Toast({ message, onClose }) {
  if (!message) return null;
  return (
    <div className="fixed right-4 top-4 z-50 rounded-xl bg-brandRed px-4 py-3 text-sm font-medium text-white shadow-card">
      <div className="flex items-center gap-3">
        <span>{message}</span>
        <button className="text-xs text-white/80" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const initialize = useAuthStore((state) => state.initialize);
  const [toast, setToast] = useState("");

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    let timeout;
    const onToast = (event) => {
      setToast(event.detail?.message ?? "Server error");
      clearTimeout(timeout);
      timeout = setTimeout(() => setToast(""), 3000);
    };
    window.addEventListener("app:toast", onToast);
    return () => {
      window.removeEventListener("app:toast", onToast);
      clearTimeout(timeout);
    };
  }, []);

  return (
    <div className="mx-auto min-h-screen max-w-3xl bg-brandCream pb-20 font-body text-[#1c1c1c]">
      <Toast message={toast} onClose={() => setToast("")} />
      <Suspense fallback={<div className="px-4 py-6 text-sm text-gray-500">Loading...</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route
            path="/user/home"
            element={
              <ProtectedRoute allowedRoles={["user"]}>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/user/food/:id"
            element={
              <ProtectedRoute allowedRoles={["user"]}>
                <FoodDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/user/cart"
            element={
              <ProtectedRoute allowedRoles={["user"]}>
                <Cart />
              </ProtectedRoute>
            }
          />
          <Route
            path="/user/checkout"
            element={
              <ProtectedRoute allowedRoles={["user"]}>
                <Checkout />
              </ProtectedRoute>
            }
          />
          <Route
            path="/user/orders"
            element={
              <ProtectedRoute allowedRoles={["user"]}>
                <UserOrders />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/menu"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminMenu />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/orders"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminOrders />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminUsers />
              </ProtectedRoute>
            }
          />

          <Route
            path="/rider/dashboard"
            element={
              <ProtectedRoute allowedRoles={["rider", "admin"]}>
                <RiderDashboard />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Suspense>
    </div>
  );
}
