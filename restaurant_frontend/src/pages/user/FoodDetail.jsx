import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import { useCartStore } from "../../stores/cartStore";

function resolveImageUrl(imageUrl) {
  if (!imageUrl) return "";
  if (imageUrl.startsWith("http")) return imageUrl;
  const base = axiosInstance.getBaseUrl();
  return `${base}${imageUrl.startsWith("/") ? "" : "/"}${imageUrl}`;
}

export default function FoodDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [food, setFood] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const addToCart = useCartStore((state) => state.addToCart);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError("");
    axiosInstance
      .get(`/foods/${id}`)
      .then((response) => {
        if (!mounted) return;
        setFood(response.data);
      })
      .catch((err) => {
        if (!mounted) return;
        setFood(null);
        setError(err.response?.data?.detail || "Could not load meal details.");
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [id]);

  return (
    <main className="page-wrapper bg-gray-50/30">
      <Navbar title="Meal Details" />
      
      <section className="mx-auto max-w-lg pb-28 pt-4 fade-up">
        <button 
          onClick={() => navigate(-1)}
          className="mx-4 mb-4 flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-gray-900 transition-colors"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>
          Back to Menu
        </button>

        {loading ? (
          <div className="mx-4 rounded-[2rem] bg-white p-5 shadow-[0_8px_30px_rgba(0,0,0,0.04)] animate-pulse border border-gray-100">
            <div className="h-64 rounded-3xl bg-gray-100" />
            <div className="mt-6 h-8 w-3/4 rounded-lg bg-gray-100" />
            <div className="mt-4 h-4 w-full rounded bg-gray-100" />
            <div className="mt-2 h-4 w-5/6 rounded bg-gray-100" />
            <div className="mt-8 flex justify-between items-end">
              <div className="h-8 w-1/3 rounded-lg bg-gray-100" />
              <div className="h-14 w-1/2 rounded-2xl bg-gray-100" />
            </div>
          </div>
        ) : error ? (
          <div className="mx-4 rounded-2xl bg-red-50 p-6 text-center text-red-600 border border-red-100">
            <span className="text-3xl block mb-2">⚠️</span>
            <p className="font-semibold">{error}</p>
          </div>
        ) : food ? (
          <div className="mx-4 overflow-hidden rounded-[2.5rem] bg-white shadow-[0_12px_40px_rgba(0,0,0,0.06)] border border-gray-100 relative">
            <div className="relative h-72 w-full bg-brandCream overflow-hidden">
              {food.image_url ? (
                <img
                  src={resolveImageUrl(food.image_url)}
                  alt={food.name}
                  className="h-full w-full object-cover transition-transform duration-700 hover:scale-105"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-6xl opacity-30">🍽️</div>
              )}
              
              {!food.is_available && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                  <span className="rounded-full bg-white px-6 py-2 text-sm font-black uppercase tracking-widest text-gray-900 shadow-xl">
                    Sold Out
                  </span>
                </div>
              )}
              
              {/* Decorative gradient overlay */}
              <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/40 to-transparent pointer-events-none" />
            </div>
            
            <div className="p-8 relative">
              {/* Floating Price Tag */}
              <div className="absolute -top-7 right-8 rounded-2xl bg-white p-2 shadow-xl shadow-black/5 border border-gray-100">
                <div className="rounded-xl bg-brandRed px-4 py-2">
                  <p className="font-heading text-[22px] font-black tracking-tight text-white shadow-sm">
                    ₦{Number(food.price).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="mt-2 pr-20">
                <h2 className="font-heading text-3xl font-black leading-tight text-gray-900">
                  {food.name}
                </h2>
              </div>
              
              <div className="mt-6 border-t border-gray-100 pt-6">
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-3">Description</h3>
                <p className="text-base text-gray-600 leading-relaxed font-medium">
                  {food.description || "A delicious, authentic Nigerian meal prepared fresh daily using premium ingredients and traditional spices."}
                </p>
              </div>

              <div className="mt-10">
                <button
                  className="btn-primary w-full py-4 text-[17px] shadow-[0_10px_25px_rgba(232,34,10,0.3)] disabled:opacity-50 disabled:shadow-none"
                  onClick={() => addToCart(food, 1)}
                  disabled={!food.is_available}
                >
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="mr-2"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
                  {food.is_available ? "Add to Cart" : "Currently Unavailable"}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="mx-4 rounded-3xl bg-white p-10 text-center shadow-sm">
            <span className="text-4xl block mb-4 opacity-50">🔍</span>
            <p className="text-gray-500 font-medium text-lg">Meal not found.</p>
          </div>
        )}
      </section>
      
      <BottomNav role="user" />
    </main>
  );
}
