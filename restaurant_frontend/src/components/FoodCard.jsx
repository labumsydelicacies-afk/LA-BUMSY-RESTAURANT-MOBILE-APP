import { Link } from "react-router-dom";
import axiosInstance from "../api/axiosInstance";
import { useCartStore } from "../stores/cartStore";

function resolveImageUrl(imageUrl) {
  if (!imageUrl) return "";
  if (imageUrl.startsWith("http")) return imageUrl;
  const base = axiosInstance.getBaseUrl();
  return `${base}${imageUrl.startsWith("/") ? "" : "/"}${imageUrl}`;
}

export default function FoodCard({ food }) {
  const addToCart = useCartStore((state) => state.addToCart);

  return (
    <article className="group relative flex flex-col justify-between overflow-hidden rounded-[24px] bg-white p-3 shadow-[0_8px_24px_rgba(0,0,0,0.04)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_16px_40px_rgba(232,34,10,0.08)] border border-gray-100">
      <Link to={`/user/food/${food.id}`} className="block relative overflow-hidden rounded-2xl h-40 w-full bg-brandCream">
        {food.image_url ? (
          <img
            src={resolveImageUrl(food.image_url)}
            alt={food.name}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-4xl opacity-50 transition-transform duration-500 group-hover:scale-110">
            🍽️
          </div>
        )}
        
        {/* Availability Badge */}
        {!food.is_available && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[2px]">
            <span className="rounded-full bg-white/90 px-3 py-1 text-xs font-bold uppercase tracking-wider text-gray-800 shadow-sm">
              Sold Out
            </span>
          </div>
        )}
      </Link>
      
      <div className="flex flex-1 flex-col pt-4 pb-2 px-1">
        <Link to={`/user/food/${food.id}`} className="block flex-1">
          <h3 className="font-heading text-[17px] font-extrabold leading-tight text-gray-900 line-clamp-1 group-hover:text-brandRed transition-colors">
            {food.name}
          </h3>
          <p className="mt-1.5 line-clamp-2 text-[13px] text-gray-500 font-medium leading-relaxed">
            {food.description || "Delicious authentic Nigerian meal."}
          </p>
        </Link>
        
        <div className="mt-4 flex items-center justify-between">
          <p className="font-heading text-[18px] font-extrabold text-brandRed">
            ₦{Number(food.price).toLocaleString()}
          </p>
          
          {food.is_available ? (
            <button
              className="flex h-10 w-10 items-center justify-center rounded-full bg-brandRed text-white shadow-[0_4px_12px_rgba(232,34,10,0.3)] transition-all duration-200 hover:scale-110 hover:bg-[#c41a07] active:scale-95"
              onClick={(e) => {
                e.preventDefault();
                addToCart(food, 1);
              }}
              aria-label="Add to cart"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            </button>
          ) : (
            <div className="h-10 w-10" /> /* Spacer */
          )}
        </div>
      </div>
    </article>
  );
}
