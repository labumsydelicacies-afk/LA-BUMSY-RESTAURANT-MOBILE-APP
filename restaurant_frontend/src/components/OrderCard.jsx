const STATUS_COLORS = {
  pending: "bg-amber-100 text-amber-800 border-amber-200",
  confirmed: "bg-blue-100 text-blue-800 border-blue-200",
  preparing: "bg-purple-100 text-purple-800 border-purple-200",
  ready: "bg-indigo-100 text-indigo-800 border-indigo-200",
  picked_up: "bg-cyan-100 text-cyan-800 border-cyan-200",
  delivered: "bg-emerald-100 text-emerald-800 border-emerald-200",
  cancelled: "bg-rose-100 text-rose-800 border-rose-200",
};

const STATUS_LABELS = {
  pending: "Pending",
  confirmed: "Confirmed",
  preparing: "Preparing",
  ready: "Ready for Pickup",
  picked_up: "On the way",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

export default function OrderCard({ order, children }) {
  const status = String(order.status || "pending").toLowerCase();
  const statusStyle = STATUS_COLORS[status] || "bg-gray-100 text-gray-800 border-gray-200";
  const statusLabel = STATUS_LABELS[status] || order.status;
  const orderIdLabel = order?.id ? String(order.id).slice(-6) : "N/A";

  return (
    <article className="rounded-3xl bg-white p-5 shadow-[0_8px_24px_rgba(0,0,0,0.04)] transition-all hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)] border border-gray-100 relative overflow-hidden">
      {/* Decorative side accent based on status */}
      <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${statusStyle.split(' ')[0].replace('100', '400')}`} />
      
      <div className="mb-4 flex items-start justify-between">
        <div>
          <p className="font-heading text-lg font-black tracking-tight text-gray-900">
            Order #{orderIdLabel}
          </p>
          <p className="mt-1 text-xs font-medium text-gray-500">
            {new Date(order.created_at).toLocaleString('en-US', {
              month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
            })}
          </p>
        </div>
        
        <span className={`rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wider ${statusStyle}`}>
          {statusLabel}
        </span>
      </div>
      
      <div className="flex items-center justify-between mt-2 pt-4 border-t border-dashed border-gray-200">
        <p className="text-sm font-semibold text-gray-500">Total Amount</p>
        <p className="font-heading text-xl font-extrabold text-brandRed">
          ₦{Number(order.total_price).toLocaleString()}
        </p>
      </div>

      {children ? <div className="mt-4 pt-2">{children}</div> : null}
    </article>
  );
}
