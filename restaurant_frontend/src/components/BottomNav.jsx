import { memo, useMemo } from "react";
import { NavLink } from "react-router-dom";
import { useCartStore } from "../stores/cartStore";

// Reusable SVG icons
const Icons = {
  Home: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>,
  Cart: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>,
  Orders: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>,
  Dashboard: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>,
  Menu: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
};

function BottomNav({ role = "user" }) {
  const cartItems = useCartStore((state) => state.items);
  const cartCount = useMemo(
    () => cartItems.reduce((acc, item) => acc + item.quantity, 0),
    [cartItems]
  );

  const linksByRole = {
    user: [
      { label: "Home", to: "/user/home", icon: Icons.Home },
      { label: "Cart", to: "/user/cart", icon: Icons.Cart, badge: cartCount },
      { label: "Orders", to: "/user/orders", icon: Icons.Orders },
    ],
    admin: [
      { label: "Overview", to: "/admin/dashboard", icon: Icons.Dashboard },
      { label: "Menu", to: "/admin/menu", icon: Icons.Menu },
      { label: "Orders", to: "/admin/orders", icon: Icons.Orders },
    ],
    rider: [
      { label: "Dashboard", to: "/rider/dashboard", icon: Icons.Dashboard }
    ],
  };

  const links = linksByRole[role] || linksByRole.user;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 flex justify-center px-4 pointer-events-none pb-[max(0.75rem,env(safe-area-inset-bottom))]">
      <nav className="flex w-full max-w-sm items-center justify-around rounded-[2rem] bg-white/90 p-2 shadow-[0_12px_40px_rgba(0,0,0,0.1)] backdrop-blur-xl border border-white pointer-events-auto">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `relative flex flex-col items-center justify-center rounded-full px-5 py-2.5 transition-all duration-300 ease-out
                ${isActive 
                  ? "bg-brandRed text-white shadow-[0_4px_15px_rgba(232,34,10,0.3)] scale-105" 
                  : "text-gray-400 hover:text-gray-900 hover:bg-gray-50"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <div className={`transition-transform duration-300 ${isActive ? '-translate-y-0.5' : ''}`}>
                    <Icon />
                  </div>
                  
                  {isActive && (
                    <span className="mt-1 text-[10px] font-bold tracking-wide uppercase block w-full text-center fade-up">
                      {link.label}
                    </span>
                  )}

                  {link.badge > 0 && !isActive && (
                    <span className="absolute right-3 top-2 flex h-4 w-4 items-center justify-center rounded-full bg-brandRed text-[10px] font-bold text-white shadow-sm ring-2 ring-white">
                      {link.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}

export default memo(BottomNav);
