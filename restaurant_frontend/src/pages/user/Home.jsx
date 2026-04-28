import { useEffect, useState, useCallback } from "react";
import axiosInstance from "../../api/axiosInstance";
import FoodCard from "../../components/FoodCard";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";
import { useSocketStore } from "../../stores/socketStore";

export default function Home() {
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  
  const connect = useSocketStore((state) => state.connect);
  const disconnect = useSocketStore((state) => state.disconnect);

  const fetchFoods = useCallback(async () => {
    try {
      const { data } = await axiosInstance.get("/foods");
      setFoods(Array.isArray(data) ? data : data.foods || []);
      setError("");
    } catch (err) {
      setFoods([]);
      setError(err.response?.data?.detail || "Could not load menu right now.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFoods();
    connect({ onFoodUpdated: fetchFoods });
    return () => disconnect();
  }, [fetchFoods, connect, disconnect]);

  const filtered = foods.filter((f) =>
    f.name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <main className="page-wrapper relative overflow-x-hidden">
      <Navbar />
      
      {/* Hero Section */}
      <section className="relative mx-4 mt-6 mb-8 overflow-hidden rounded-[2rem] bg-gradient-to-br from-brandRed via-[#c41a07] to-[#8B1104] p-8 text-white shadow-[0_15px_30px_rgba(232,34,10,0.3)]">
        <div className="relative z-10 max-w-sm fade-up">
          <span className="mb-3 inline-block rounded-full bg-white/20 px-4 py-1.5 text-xs font-bold tracking-wider backdrop-blur-md">
            🔥 HOT & FRESH
          </span>
          <h1 className="font-heading text-4xl font-extrabold leading-[1.1] md:text-5xl">
            Taste Nigeria,<br />
            <span className="text-brandYellow">One Plate</span> at a Time.
          </h1>
          <p className="mt-4 text-sm font-medium text-white/90 leading-relaxed max-w-[280px]">
            Authentic Nigerian dishes made with love, delivered straight to your door in minutes.
          </p>
        </div>
        
        {/* Decorative elements */}
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full border-[40px] border-white/5 opacity-50 blur-sm" />
        <div className="absolute -bottom-24 right-10 h-48 w-48 rounded-full bg-brandYellow/20 blur-2xl" />
      </section>

      {/* Search Bar */}
      <section className="mx-4 mb-8 fade-up" style={{ animationDelay: '0.1s' }}>
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-brandRed transition-colors">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </div>
          <input
            type="search"
            placeholder="What are you craving today?"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white/80 backdrop-blur-xl border-2 border-transparent focus:border-brandRed/20 focus:bg-white shadow-[0_8px_20px_rgba(0,0,0,0.04)] rounded-2xl py-4 pl-12 pr-4 outline-none text-gray-800 placeholder:text-gray-400 font-medium transition-all"
          />
        </div>
      </section>

      {/* Menu Grid */}
      <section className="px-4 pb-12 fade-up" style={{ animationDelay: '0.2s' }}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="section-title !mb-0">Popular Menu</h2>
          <span className="text-sm font-bold text-brandRed bg-brandRed/10 px-3 py-1 rounded-full">{filtered.length} items</span>
        </div>
        
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="rounded-3xl bg-white p-3 shadow-card animate-pulse border border-gray-100">
                <div className="h-32 rounded-2xl bg-gray-100 mb-4" />
                <div className="h-4 w-3/4 rounded-md bg-gray-100 mb-2" />
                <div className="h-3 w-1/2 rounded-md bg-gray-100 mb-4" />
                <div className="flex justify-between items-center">
                  <div className="h-5 w-1/3 rounded-md bg-gray-100" />
                  <div className="h-10 w-10 rounded-full bg-gray-100" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="rounded-2xl bg-red-50 p-6 text-center text-red-600 border border-red-100">
            <span className="text-3xl block mb-2">⚠️</span>
            <p className="font-semibold">{error}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-3xl bg-white/50 backdrop-blur-md p-10 text-center shadow-sm border border-white">
            <span className="text-5xl block mb-4 opacity-50">🍽️</span>
            <p className="font-heading text-xl font-bold text-gray-700 mb-2">No dishes found</p>
            <p className="text-gray-500 text-sm">We couldn't find any meals matching your search.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {filtered.map((food, idx) => (
              <div key={food.id} className="fade-up" style={{ animationDelay: `${0.1 + (idx * 0.05)}s` }}>
                <FoodCard food={food} />
              </div>
            ))}
          </div>
        )}
      </section>
      <BottomNav role="user" />
    </main>
  );
}
