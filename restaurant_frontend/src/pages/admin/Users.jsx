import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";

// ─── Role Badge ──────────────────────────────────────────────────────────────
function RoleBadge({ label, active, color }) {
  const colors = {
    red:    "bg-rose-100 text-rose-700 border-rose-200",
    blue:   "bg-blue-100 text-blue-700 border-blue-200",
    cyan:   "bg-cyan-100 text-cyan-700 border-cyan-200",
    gray:   "bg-gray-100 text-gray-400 border-gray-200",
  };
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${active ? colors[color] : colors.gray}`}>
      {label}
    </span>
  );
}

// ─── Role Switcher Row ───────────────────────────────────────────────────────
function RoleSwitcher({ user, onUpdate, busy }) {
  const roles = [
    { label: "Customer", field: "customer" },
    { label: "Rider",    field: "rider" },
    { label: "Admin",    field: "admin" },
  ];

  const current = user.is_admin ? "admin" : user.is_rider ? "rider" : "customer";

  const handleSelect = (role) => {
    if (role === current || busy) return;
    onUpdate(user.id, {
      is_admin: role === "admin",
      is_rider: role === "rider",
    });
  };

  return (
    <div className="mt-3 flex rounded-xl bg-gray-100 p-0.5 gap-0.5">
      {roles.map((r) => (
        <button
          key={r.field}
          type="button"
          onClick={() => handleSelect(r.field)}
          disabled={busy}
          className={`flex-1 rounded-[10px] py-1.5 text-xs font-bold transition-all duration-200 disabled:opacity-50 ${
            current === r.field
              ? "bg-brandRed text-white shadow-sm"
              : "text-gray-500 hover:text-gray-700 hover:bg-gray-200"
          }`}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}

// ─── User Card ───────────────────────────────────────────────────────────────
function UserCard({ user, onUpdate, busy }) {
  return (
    <article className="rounded-2xl bg-white p-4 shadow-[0_4px_16px_rgba(0,0,0,0.05)] border border-gray-100">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-heading text-sm font-black text-gray-900">@{user.nickname}</p>
          <p className="truncate text-xs text-gray-400">{user.email}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-1 justify-end">
          {user.is_admin && <RoleBadge label="Admin" active color="red" />}
          {user.is_rider && <RoleBadge label="Rider" active color="cyan" />}
          {!user.is_admin && !user.is_rider && <RoleBadge label="Customer" active color="blue" />}
          {!user.is_verified && <RoleBadge label="Unverified" active color="gray" />}
        </div>
      </div>
      <RoleSwitcher user={user} onUpdate={onUpdate} busy={busy === user.id} />
    </article>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────
export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);   // user_id being updated
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [search, setSearch] = useState("");

  const fetchUsers = async () => {
    try {
      const { data } = await axiosInstance.get("/admin/users");
      setUsers(Array.isArray(data) ? data : []);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load users.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleUpdate = async (userId, payload) => {
    try {
      setBusy(userId);
      setError("");
      const { data } = await axiosInstance.patch(`/admin/users/${userId}/role`, payload);
      setUsers((prev) => prev.map((u) => (u.id === data.id ? data : u)));
      setSuccessMsg("Role updated.");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update role.");
    } finally {
      setBusy(null);
    }
  };

  const filtered = users.filter((u) => {
    const q = search.toLowerCase();
    return (
      u.nickname?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q)
    );
  });

  return (
    <main>
      <Navbar title="User management" />
      <section className="space-y-3 px-4 pb-24 pt-3">

        {/* Search */}
        <input
          type="search"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full box-border rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none transition focus:border-brandRed focus:ring-2 focus:ring-brandRed/20"
        />

        {/* Feedback */}
        {error ? (
          <p className="rounded-xl bg-rose-50 px-4 py-2.5 text-sm font-medium text-brandRed border border-rose-100">
            {error}
          </p>
        ) : null}
        {successMsg ? (
          <p className="rounded-xl bg-emerald-50 px-4 py-2.5 text-sm font-medium text-emerald-700 border border-emerald-100">
            {successMsg}
          </p>
        ) : null}

        {/* Stats strip */}
        {!loading && users.length > 0 ? (
          <div className="flex gap-2 text-xs text-gray-500 font-medium">
            <span>{users.length} total</span>
            <span>·</span>
            <span>{users.filter((u) => u.is_rider).length} riders</span>
            <span>·</span>
            <span>{users.filter((u) => u.is_admin).length} admins</span>
          </div>
        ) : null}

        {/* User list */}
        {loading ? (
          <p className="text-sm text-gray-500">Loading users…</p>
        ) : filtered.length === 0 ? (
          <p className="text-sm text-gray-400">No users found.</p>
        ) : (
          <div className="space-y-2">
            {filtered.map((user) => (
              <UserCard
                key={user.id}
                user={user}
                onUpdate={handleUpdate}
                busy={busy}
              />
            ))}
          </div>
        )}

      </section>
      <BottomNav role="admin" />
    </main>
  );
}
