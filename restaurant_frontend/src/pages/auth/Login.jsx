import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

const redirectByRole = {
  user: "/user/home",
  admin: "/admin/dashboard",
  rider: "/rider/dashboard",
};

export default function Login() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const role = useAuthStore((state) => state.role);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setLoading(true);
      setError("");
      const role = await login(email, password);
      navigate(redirectByRole[role] || "/user/home");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && role) {
      navigate(redirectByRole[role] || "/user/home");
    }
  }, [isAuthenticated, role, navigate]);

  return (
    <main className="auth-food-bg relative flex min-h-screen items-center justify-center px-4 py-8">
      <section className="auth-card w-full max-w-md rounded-3xl bg-white/95 p-6 shadow-card sm:p-7">
        <div className="mb-8 rounded-2xl bg-brandRed p-5 text-white">
          <h1 className="font-heading text-3xl font-extrabold">La Bumsy Delicacies</h1>
          <p className="mt-2 text-sm text-white/90">Welcome back. Sign in to order your favorite meals.</p>
        </div>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block">
            <span className="mb-1 block text-xs font-semibold uppercase text-gray-500">Email</span>
            <input
              type="email"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-semibold uppercase text-gray-500">Password</span>
            <input
              type="password"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error ? <p className="text-sm text-brandRed">{error}</p> : null}
          <button
            type="submit"
            className="w-full rounded-xl bg-brandRed py-3 font-semibold text-white transition hover:bg-red-700 disabled:opacity-70"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                Signing in...
              </span>
            ) : "Sign In"}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-gray-600">
          New here?{" "}
          <Link to="/register" className="font-semibold text-brandRed">
            Create account
          </Link>
        </p>
      </section>
    </main>
  );
}
