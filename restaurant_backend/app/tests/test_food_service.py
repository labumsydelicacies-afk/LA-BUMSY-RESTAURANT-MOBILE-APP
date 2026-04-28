"""Ad-hoc smoke tests for the food service layer."""

from app.schemas.food import FoodCreate, FoodUpdate
from app.services.food_service import (
    create_food,
    delete_food,
    get_all_foods,
    get_all_foods_admin,
    get_food_by_id,
    get_food_by_name,
    toggle_availability,
    update_food,
)
from app.tests.helpers import configure_output, db_session, print_footer, print_header


def main() -> None:
    configure_output()
    print_header("FOOD SERVICE LAYER TEST")

    with db_session() as db:
        new_food = None
        test_food_name = "Amala and ewedu"
        test_food_desc = "A delicious test dish."
        test_food_price = 9.99
        test_food_image = "https://example.com/test-food.jpg"

        try:
            print("\n[TEST 1] Creating a new food item...")
            new_food = create_food(
                db,
                FoodCreate(
                    name=test_food_name,
                    description=test_food_desc,
                    price=test_food_price,
                    image_url=test_food_image,
                    is_available=True,
                ),
            )
            print(f"  Created       : {new_food.name}")
            print(f"  Price         : ${new_food.price}")
            print(f"  Is Available  : {new_food.is_available}")

            print("\n[TEST 2] Creating duplicate food item (should fail)...")
            try:
                create_food(
                    db,
                    FoodCreate(
                        name=test_food_name,
                        description="duplicate",
                        price=5.99,
                        image_url=test_food_image,
                        is_available=True,
                    ),
                )
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 3] Creating food with invalid price (should fail)...")
            try:
                create_food(
                    db,
                    FoodCreate(
                        name="Invalid Price Food",
                        description="bad price",
                        price=-5.00,
                        image_url=test_food_image,
                        is_available=True,
                    ),
                )
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 4] Fetching all available food items...")
            foods = get_all_foods(db)
            print(f"  Available foods : {len(foods)}")
            for food in foods:
                print(f"     - {food.name} (${food.price}) | Available : {food.is_available}")

            print("\n[TEST 5] Fetching all food items as admin...")
            all_foods = get_all_foods_admin(db)
            print(f"  Total foods in DB : {len(all_foods)}")

            print("\n[TEST 6] Fetching food by ID...")
            food = get_food_by_id(db, new_food.id)
            if food:
                print(f"  Found : {food.name} (ID: {food.id})")
            else:
                print("  Food not found")

            print("\n[TEST 7] Fetching food by name...")
            food_by_name = get_food_by_name(db, test_food_name)
            if food_by_name:
                print(f"  Found : {food_by_name.name} (ID: {food_by_name.id})")
            else:
                print("  Food not found")

            print("\n[TEST 8] Updating food item...")
            updated_food = update_food(
                db,
                new_food.id,
                FoodUpdate(price=12.99, description="Updated description"),
            )
            print(f"  Updated price       : ${updated_food.price}")
            print(f"  Updated description : {updated_food.description}")

            print("\n[TEST 9] Toggling food availability...")
            toggled = toggle_availability(db, new_food.id)
            print(f"  Availability toggled : {not toggled.is_available} -> {toggled.is_available}")

            print("\n[TEST 10] Deleting food item...")
            deleted = delete_food(db, new_food.id)
            print(f"  Food deleted : {deleted}")
            new_food = None

            print("\n[TEST 11] Deleting non existent food (should fail)...")
            try:
                delete_food(db, 99999)
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

        except Exception as exc:
            print(f"\n  Unexpected error : {exc}")
            raise
        finally:
            if new_food is not None:
                try:
                    delete_food(db, new_food.id)
                except Exception:
                    db.rollback()

    print_footer()


if __name__ == "__main__":
    main()
