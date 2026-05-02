import { useState } from "react";
import { useAuthStore } from "../stores/authStore";

export default function ProfileModal({ isForced = false, onClose }) {
  const user = useAuthStore((state) => state.user);
  const completeProfile = useAuthStore((state) => state.completeProfile);
  const updateProfile = useAuthStore((state) => state.updateProfile);

  const [form, setForm] = useState({
    nickname: user?.nickname || "",
    phone: user?.phone || "",
    address: user?.address || "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isForced) {
        await completeProfile(form);
      } else {
        await updateProfile(form);
        if (onClose) onClose();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save profile");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-xl">
        <h2 className="font-heading text-xl font-bold">
          {isForced ? "Complete Your Profile" : "Edit Profile"}
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          {isForced
            ? "Please provide your details before continuing."
            : "Update your personal information."}
        </p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold text-gray-600">
              Nickname
            </label>
            <input
              name="nickname"
              value={form.nickname}
              onChange={handleChange}
              placeholder="e.g. John"
              required
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none transition focus:border-brandRed focus:bg-white focus:ring-2 focus:ring-brandRed/20"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-gray-600">
              Phone Number
            </label>
            <input
              name="phone"
              value={form.phone}
              onChange={handleChange}
              placeholder="08012345678"
              required
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none transition focus:border-brandRed focus:bg-white focus:ring-2 focus:ring-brandRed/20"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-gray-600">
              Delivery Address
            </label>
            <textarea
              name="address"
              value={form.address}
              onChange={handleChange}
              placeholder="Your full delivery address"
              required
              rows={3}
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none transition focus:border-brandRed focus:bg-white focus:ring-2 focus:ring-brandRed/20"
            />
          </div>

          {error && <p className="text-sm font-medium text-red-500">{error}</p>}

          <div className="flex gap-3 pt-2">
            {!isForced && (
              <button
                type="button"
                onClick={onClose}
                className="flex-1 rounded-xl bg-gray-100 py-3 font-semibold text-gray-600 hover:bg-gray-200"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-xl bg-brandRed py-3 font-semibold text-white transition hover:bg-red-700 disabled:opacity-70"
            >
              {loading ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
