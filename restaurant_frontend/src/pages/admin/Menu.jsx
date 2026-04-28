import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosInstance";
import Navbar from "../../components/Navbar";
import BottomNav from "../../components/BottomNav";

const emptyForm = { name: "", description: "", price: "", image_url: "" };

export default function Menu() {
  const [foods, setFoods] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [loadingDelete, setLoadingDelete] = useState({});
  const [loadingEdit, setLoadingEdit] = useState({});
  const [loadingToggle, setLoadingToggle] = useState({});
  const [error, setError] = useState("");

  const fetchFoods = async () => {
    try {
      const { data } = await axiosInstance.get("/foods/admin");
      setFoods(Array.isArray(data) ? data : []);
      setError("");
    } catch (err) {
      setFoods([]);
      setError(err.response?.data?.detail || "Could not load menu items.");
    }
  };

  useEffect(() => {
    fetchFoods();
  }, []);

  const handleCreate = async (event) => {
    event.preventDefault();
    try {
      setLoading(true);
      setError("");
      await axiosInstance.post("/foods", { ...form, price: Number(form.price) });
      setForm(emptyForm);
      await fetchFoods();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create food item.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      setLoadingDelete((prev) => ({ ...prev, [id]: true }));
      setError("");
      await axiosInstance.delete(`/foods/${id}`);
      await fetchFoods();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not delete food item.");
    } finally {
      setLoadingDelete((prev) => ({ ...prev, [id]: false }));
    }
  };

  const handleEdit = async (food) => {
    const name = window.prompt("Food name", food.name);
    if (!name) return;
    const priceInput = window.prompt("Price", String(food.price));
    if (!priceInput) return;
    const description = window.prompt("Description", food.description || "") ?? "";
    try {
      setLoadingEdit((prev) => ({ ...prev, [food.id]: true }));
      setError("");
      await axiosInstance.put(`/foods/${food.id}`, {
        name,
        description,
        price: Number(priceInput),
        image_url: food.image_url || "",
        is_available: food.is_available,
      });
      await fetchFoods();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update food item.");
    } finally {
      setLoadingEdit((prev) => ({ ...prev, [food.id]: false }));
    }
  };

  const handleToggle = async (id) => {
    try {
      setLoadingToggle((prev) => ({ ...prev, [id]: true }));
      setError("");
      await axiosInstance.patch(`/foods/${id}/toggle-availability`);
      await fetchFoods();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not toggle availability.");
    } finally {
      setLoadingToggle((prev) => ({ ...prev, [id]: false }));
    }
  };

  return (
    <main>
      <Navbar title="Manage menu" />
      <section className="space-y-4 px-4 pb-24 pt-2">
        {error ? <p className="text-sm text-brandRed">{error}</p> : null}
        <form className="space-y-2 rounded-xl bg-white p-4 shadow-card" onSubmit={handleCreate}>
          <h2 className="font-heading text-lg font-bold">Add Food</h2>
          <input
            placeholder="Name"
            className="w-full rounded-lg border px-3 py-2 text-sm"
            value={form.name}
            onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            required
          />
          <input
            placeholder="Description"
            className="w-full rounded-lg border px-3 py-2 text-sm"
            value={form.description}
            onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
          />
          <input
            placeholder="Price"
            type="number"
            min="1"
            className="w-full rounded-lg border px-3 py-2 text-sm"
            value={form.price}
            onChange={(e) => setForm((prev) => ({ ...prev, price: e.target.value }))}
            required
          />
          <input
            placeholder="Image URL / upload path"
            className="w-full rounded-lg border px-3 py-2 text-sm"
            value={form.image_url}
            onChange={(e) => setForm((prev) => ({ ...prev, image_url: e.target.value }))}
          />
          <button className="w-full rounded-lg bg-brandRed py-2 text-sm font-semibold text-white" disabled={loading}>
            {loading ? "Saving..." : "Create Food"}
          </button>
        </form>

        {foods.map((food) => (
          <article key={food.id} className="rounded-xl bg-white p-4 shadow-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-heading font-bold">{food.name}</p>
                <p className="text-sm text-gray-500">N{Number(food.price).toLocaleString()}</p>
                <p className="text-xs text-gray-500">{food.is_available ? "Available" : "Unavailable"}</p>
              </div>
               <div className="flex gap-2">
                 <button
                   className="rounded-lg border px-2 py-1 text-xs disabled:opacity-50"
                   onClick={() => handleEdit(food)}
                   disabled={loadingEdit[food.id]}
                 >
                   {loadingEdit[food.id] ? "Saving..." : "Edit"}
                 </button>
                 <button
                   className="rounded-lg border border-brandYellow px-2 py-1 text-xs disabled:opacity-50"
                   onClick={() => handleToggle(food.id)}
                   disabled={loadingToggle[food.id]}
                 >
                   {loadingToggle[food.id] ? "Updating..." : "Toggle"}
                 </button>
                 <button
                   className="rounded-lg border border-brandRed px-2 py-1 text-xs text-brandRed disabled:opacity-50"
                   onClick={() => handleDelete(food.id)}
                   disabled={loadingDelete[food.id]}
                 >
                   {loadingDelete[food.id] ? "Deleting..." : "Delete"}
                 </button>
               </div>
            </div>
          </article>
        ))}
      </section>
      <BottomNav role="admin" />
    </main>
  );
}
