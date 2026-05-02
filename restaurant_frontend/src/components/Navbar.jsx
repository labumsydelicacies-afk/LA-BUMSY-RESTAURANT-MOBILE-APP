import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";
import { useCartStore } from "../stores/cartStore";
import ProfileModal from "./ProfileModal";

export default function Navbar({ title }) {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const cartItems = useCartStore((state) => state.items);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  
  const cartCount = cartItems.reduce((acc, item) => acc + item.quantity, 0);
  const nickname = user?.nickname?.trim() || "User";
  const initial = nickname.charAt(0).toUpperCase();
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    await new Promise(r => setTimeout(r, 500));
    logout();
    navigate("/login");
  };

  return (
    <>
      <header className="sticky top-0 z-50 flex items-center justify-between bg-white/80 px-5 py-4 backdrop-blur-xl shadow-[0_4px_20px_rgba(0,0,0,0.03)] border-b border-gray-100">
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-brandYellow"></div>
            <p className="font-heading text-xl font-black tracking-tight text-brandRed">
              La Bumsy
            </p>
          </div>
          {title ? (
            <p className="mt-0.5 text-xs font-medium text-gray-500">{title}</p>
          ) : null}
        </div>
        
        <div className="flex items-center gap-3">
          <div 
            className="flex items-center gap-2 cursor-pointer transition hover:opacity-80 bg-gray-50 rounded-full pl-1 pr-3 py-1 ring-1 ring-inset ring-gray-200" 
            onClick={() => setIsProfileOpen(true)}
            title="Edit Profile"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brandRed text-sm font-bold text-white shadow-sm">
              {initial}
            </div>
            <div className="flex flex-col hidden sm:flex">
              <p className="text-[11px] font-bold text-gray-800 leading-tight">{nickname}</p>
            </div>
          </div>
        {/* Cart Icon inside Navbar for convenience */}
        <button 
          onClick={() => navigate('/user/cart')}
          className="relative rounded-full p-2 text-gray-600 transition-colors hover:bg-gray-100 active:bg-gray-200"
          aria-label="View cart"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="9" cy="21" r="1"></circle>
            <circle cx="20" cy="21" r="1"></circle>
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
          </svg>
          {cartCount > 0 && (
            <span className="absolute right-0 top-0 flex h-4 w-4 items-center justify-center rounded-full bg-brandRed text-[10px] font-bold text-white shadow-sm ring-2 ring-white">
              {cartCount}
            </span>
          )}
        </button>

        <button
          className="flex h-9 items-center justify-center gap-1.5 rounded-xl bg-gray-50 px-4 text-xs font-bold text-gray-600 shadow-sm ring-1 ring-inset ring-gray-200 transition-all hover:bg-gray-100 active:bg-gray-200 disabled:opacity-70"
          onClick={handleLogout}
          disabled={isLoggingOut}
        >
          {isLoggingOut ? (
            <svg className="animate-spin h-3.5 w-3.5 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          ) : "Logout"}
        </button>
      </div>
      </header>
      {isProfileOpen && <ProfileModal onClose={() => setIsProfileOpen(false)} />}
    </>
  );
}
