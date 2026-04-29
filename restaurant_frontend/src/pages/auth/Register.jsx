import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

export default function Register() {
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);
  const verifyOtp = useAuthStore((state) => state.verifyOtp);
  const [form, setForm] = useState({ email: "", password: "", nickname: "" });
  const [createdUser, setCreatedUser] = useState(null);
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    try {
      setLoading(true);
      setError("");
      setSuccessMessage("");
      const user = await register(form);
      setCreatedUser(user);
      setSuccessMessage(`Account created for ${user.email}. Enter the verification code sent to your email to finish setup.`);
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (event) => {
    event.preventDefault();
    if (!createdUser) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSuccessMessage("");
      await verifyOtp(createdUser.id, otp.trim());
      navigate("/login");
    } catch (err) {
      const apiMessage = err.response?.data?.detail;
      setError(
        apiMessage
          ? `${apiMessage}. Your account is created but not authenticated until OTP verification succeeds.`
          : "OTP verification failed. Your account is created but not authenticated until OTP verification succeeds."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-food-bg relative flex min-h-screen items-center justify-center px-4 py-8">
      <section className="auth-card w-full max-w-md rounded-3xl bg-white/95 p-6 shadow-card sm:p-7">
        <h1 className="font-heading text-2xl font-bold">Create account</h1>
        <p className="mt-2 text-sm text-gray-600">
          {createdUser
            ? "Your account has been created. Verify your email to finish signing up."
            : "Join La Bumsy Delicacies and start ordering."}
        </p>
        {successMessage ? (
          <p className="mt-4 rounded-2xl bg-green-50 px-4 py-3 text-sm text-green-700">
            {successMessage}
          </p>
        ) : null}
        {createdUser ? (
          <form className="mt-6 space-y-4" onSubmit={handleVerifyOtp}>
            <input
              name="otp"
              placeholder="Enter verification code"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
              value={otp}
              onChange={(event) => setOtp(event.target.value)}
              required
            />
            {error ? <p className="text-sm text-brandRed">{error}</p> : null}
            <button className="w-full rounded-xl bg-brandRed py-3 font-semibold text-white transition hover:bg-red-700 disabled:opacity-70" disabled={loading}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Verifying...
                </span>
              ) : "Verify email"}
            </button>
          </form>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={handleRegister}>
            <input
              name="nickname"
              placeholder="Nickname"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
              value={form.nickname}
              onChange={handleChange}
              required
            />
            <input
              name="email"
              type="email"
              placeholder="Email"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
              value={form.email}
              onChange={handleChange}
              required
            />
            <input
              name="password"
              type="password"
              placeholder="Password"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
            />
            {error ? <p className="text-sm text-brandRed">{error}</p> : null}
            <button className="w-full rounded-xl bg-brandRed py-3 font-semibold text-white transition hover:bg-red-700 disabled:opacity-70" disabled={loading}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Creating...
                </span>
              ) : "Create account"}
            </button>
          </form>
        )}
        <p className="mt-5 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-brandRed">
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
