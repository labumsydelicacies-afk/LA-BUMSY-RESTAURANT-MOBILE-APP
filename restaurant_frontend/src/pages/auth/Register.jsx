import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

export default function Register() {
  const OTP_LENGTH = 6;
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);
  const verifyOtp = useAuthStore((state) => state.verifyOtp);
  const resendOtp = useAuthStore((state) => state.resendOtp);
  const [selectedRole, setSelectedRole] = useState("customer");
  const [form, setForm] = useState({ email: "", password: "", nickname: "" });
  const [createdUser, setCreatedUser] = useState(null);
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const cooldownRef = useRef(null);

  const handleChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    try {
      setLoading(true);
      setError("");
      setSuccessMessage("");
      const user = await register({ ...form, role: selectedRole });
      setCreatedUser(user);
      setSuccessMessage(`Account created for ${user.email}. Email delivery is in progress. Enter the verification code when it arrives to complete authentication.`);
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

  const startCooldown = (seconds = 30) => {
    setResendCooldown(seconds);
    clearInterval(cooldownRef.current);
    cooldownRef.current = setInterval(() => {
      setResendCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(cooldownRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleResendOtp = async () => {
    if (!createdUser || resendCooldown > 0) return;
    try {
      setError("");
      await resendOtp(createdUser.email);
      setSuccessMessage("A new code has been sent to your email.");
      startCooldown(30);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not resend OTP. Please try again.");
    }
  };


  const handleOtpInput = (index, value) => {
    const cleanedValue = value.replace(/\D/g, "").slice(-1);
    const otpChars = otp.split("");
    otpChars[index] = cleanedValue;
    const nextOtp = otpChars.join("").slice(0, OTP_LENGTH);
    setOtp(nextOtp);

    if (cleanedValue && index < OTP_LENGTH - 1) {
      const nextBox = document.getElementById(`otp-box-${index + 1}`);
      nextBox?.focus();
    }
  };

  const handleOtpKeyDown = (index, event) => {
    if (event.key === "Backspace" && !otp[index] && index > 0) {
      const prevBox = document.getElementById(`otp-box-${index - 1}`);
      prevBox?.focus();
    }
  };

  const handleOtpPaste = (event) => {
    const pastedOtp = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, OTP_LENGTH);
    if (!pastedOtp) {
      return;
    }

    event.preventDefault();
    setOtp(pastedOtp);
    const focusIndex = Math.min(pastedOtp.length, OTP_LENGTH - 1);
    const focusBox = document.getElementById(`otp-box-${focusIndex}`);
    focusBox?.focus();
  };

  return (
    <main className="auth-food-bg relative flex min-h-[100dvh] items-start justify-center overflow-y-auto px-4 py-8 sm:min-h-screen sm:items-center">
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
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Enter the 6-digit verification code</p>
              <div className="flex items-center justify-between gap-2 sm:gap-3" onPaste={handleOtpPaste}>
                {Array.from({ length: OTP_LENGTH }).map((_, index) => (
                  <input
                    key={index}
                    id={`otp-box-${index}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    className="h-12 w-11 box-border rounded-xl border border-gray-200 text-center text-lg font-semibold outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20 sm:h-14 sm:w-12"
                    value={otp[index] || ""}
                    onChange={(event) => handleOtpInput(index, event.target.value)}
                    onKeyDown={(event) => handleOtpKeyDown(index, event)}
                    required
                  />
                ))}
              </div>
            </div>
            {error ? <p className="text-sm text-brandRed">{error}</p> : null}
            <button className="w-full rounded-xl bg-brandRed py-3 font-semibold text-white transition hover:bg-red-700 disabled:opacity-70" disabled={loading}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Verifying...
                </span>
              ) : "Verify email"}
            </button>
            <p className="text-center text-sm text-gray-500">
              Didn&apos;t receive a code?{" "}
              <button
                type="button"
                id="resend-otp-btn"
                className="font-semibold text-brandRed hover:underline disabled:opacity-50"
                onClick={handleResendOtp}
                disabled={resendCooldown > 0}
              >
                {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend code"}
              </button>
            </p>
          </form>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={handleRegister}>
            {/* ── Role Switcher ─────────────────────────────────────── */}
            <div>
              <p className="mb-2 text-xs font-semibold uppercase text-gray-400 tracking-wide">I want to sign up as</p>
              <div className="relative flex rounded-2xl bg-gray-100 p-1">
                {/* sliding pill */}
                <div
                  className="absolute top-1 bottom-1 w-[calc(50%-4px)] rounded-xl bg-brandRed shadow-sm transition-all duration-300 ease-out"
                  style={{ left: selectedRole === "customer" ? "4px" : "calc(50%)" }}
                />
                <button
                  type="button"
                  id="role-customer-btn"
                  className={`relative z-10 flex-1 rounded-xl py-2 text-sm font-bold transition-colors duration-200 ${
                    selectedRole === "customer" ? "text-white" : "text-gray-500 hover:text-gray-700"
                  }`}
                  onClick={() => setSelectedRole("customer")}
                >
                  🍽️ Customer
                </button>
                <button
                  type="button"
                  id="role-rider-btn"
                  className={`relative z-10 flex-1 rounded-xl py-2 text-sm font-bold transition-colors duration-200 ${
                    selectedRole === "rider" ? "text-white" : "text-gray-500 hover:text-gray-700"
                  }`}
                  onClick={() => setSelectedRole("rider")}
                >
                  🛵 Rider
                </button>
              </div>
              <p className="mt-1.5 text-xs text-gray-400 text-center">
                {selectedRole === "customer"
                  ? "Order food and track your deliveries"
                  : "Accept and deliver orders in your area"}
              </p>
            </div>
            <input
              name="nickname"
              placeholder="Nickname"
              className="w-full box-border text-left rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
              value={form.nickname}
              onChange={handleChange}
              required
            />
            <input
              name="email"
              type="email"
              placeholder="Email"
              className="w-full box-border text-left rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
              value={form.email}
              onChange={handleChange}
              required
            />
            <input
              name="password"
              type="password"
              placeholder="Password"
              className="w-full box-border text-left rounded-xl border border-gray-200 px-4 py-3 outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
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
