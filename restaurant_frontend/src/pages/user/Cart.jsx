import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import { useCartStore } from "../../stores/cartStore";

export default function Cart() {
  const items = useCartStore((state) => state.items);
  const removeFromCart = useCartStore((state) => state.removeFromCart);
  const addToCart = useCartStore((state) => state.addToCart); // Assuming we can add more
  const clearCart = useCartStore((state) => state.clearCart);
  
  const total = items.reduce((acc, item) => acc + Number(item.price || 0) * item.quantity, 0);

  return (
    <main className="page-wrapper bg-gray-50/50">
      <Navbar title="Review Your Cart" />
      
      <section className="mx-4 mt-6 mb-24 max-w-lg mx-auto fade-up">
        <div className="flex items-center justify-between mb-6">
          <h1 className="font-heading text-3xl font-extrabold text-gray-900">Your Cart</h1>
          {items.length > 0 && (
            <button 
              onClick={clearCart}
              className="text-sm font-semibold text-gray-400 hover:text-brandRed transition-colors"
            >
              Clear All
            </button>
          )}
        </div>

        {items.length === 0 ? (
          <div className="rounded-[2rem] bg-white p-12 text-center shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100">
            <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-gray-50 text-5xl">
              🛒
            </div>
            <p className="font-heading text-xl font-bold text-gray-800 mb-2">Your cart is empty</p>
            <p className="text-sm text-gray-500 mb-8">Looks like you haven't added any delicious meals yet.</p>
            <Link to="/user/home" className="btn-primary w-full">
              Browse Menu
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((item, index) => (
              <article
                key={item.id}
                className="group relative flex items-center overflow-hidden rounded-3xl bg-white p-4 shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-gray-100 transition-shadow hover:shadow-[0_8px_25px_rgba(0,0,0,0.06)] slide-up"
                style={{ animationDelay: `${index * 60}ms` }}
              >
                <div className="flex-1 min-w-0 pr-4">
                  <h3 className="font-heading text-[17px] font-bold text-gray-900 truncate">{item.name}</h3>
                  <p className="font-heading text-[15px] font-extrabold text-brandRed mt-1">
                    ₦{Number(item.price).toLocaleString()}
                  </p>
                </div>
                
                <div className="flex flex-col items-end gap-3">
                  <div className="flex items-center rounded-full bg-gray-100 p-1">
                    <button 
                      onClick={() => removeFromCart(item.id)}
                      className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-gray-600 shadow-sm transition-transform active:scale-95"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    </button>
                    <span className="w-8 text-center text-sm font-bold text-gray-800">{item.quantity}</span>
                    <button 
                      onClick={() => addToCart(item, 1)}
                      className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-brandRed shadow-sm transition-transform active:scale-95"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    </button>
                  </div>
                </div>
              </article>
            ))}

            {/* Total Section */}
            <div className="mt-8 rounded-[2rem] bg-white p-6 shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-gray-100 relative overflow-hidden">
              <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-brandRed/5 blur-2xl pointer-events-none" />
              
              <div className="space-y-3 text-sm font-medium text-gray-500 mb-4 border-b border-dashed border-gray-200 pb-4">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span className="text-gray-800">₦{total.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Delivery Fee</span>
                  <span className="text-gray-800">Calculated at checkout</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between mb-6">
                <p className="text-base font-bold text-gray-800">Total</p>
                <p className="font-heading text-3xl font-black text-brandRed">₦{total.toLocaleString()}</p>
              </div>
              
              <Link
                to="/user/checkout"
                className="btn-primary w-full shadow-[0_8px_20px_rgba(232,34,10,0.25)] py-4 text-lg"
              >
                Proceed to Checkout
              </Link>
            </div>
          </div>
        )}
      </section>
      
      <BottomNav role="user" />
    </main>
  );
}
