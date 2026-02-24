"""
Seed script: populates the database with sample data for testing.
Run: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
from auth import hash_password
import models

# Reset DB
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # ── Users ────────────────────────────────────────
    users = [
        models.User(name="Admin User", email="admin@pindrop.com", password=hash_password("password123"), role="admin", pin_code="110001"),
        models.User(name="Raj Kumar", email="raj@restaurant.com", password=hash_password("password123"), role="owner", pin_code="110001"),
        models.User(name="Priya Sharma", email="priya@restaurant.com", password=hash_password("password123"), role="owner", pin_code="110002"),
        models.User(name="Amit Singh", email="amit@customer.com", password=hash_password("password123"), role="customer", pin_code="110001"),
        models.User(name="Neha Gupta", email="neha@customer.com", password=hash_password("password123"), role="customer", pin_code="110002"),
        models.User(name="Suresh Yadav", email="suresh@delivery.com", password=hash_password("password123"), role="delivery", pin_code="110001"),
        models.User(name="Ravi Patel", email="ravi@delivery.com", password=hash_password("password123"), role="delivery", pin_code="110002"),
        models.User(name="Anita Desai", email="anita@care.com", password=hash_password("password123"), role="care", pin_code="110001"),
    ]
    db.add_all(users)
    db.commit()
    for u in users:
        db.refresh(u)

    print(f"✓ Created {len(users)} users")

    # ── Restaurants ──────────────────────────────────
    restaurants = [
        models.Restaurant(name="Spice Garden", pin_code="110001", status="active", restaurant_fee=25.0, owner_id=users[1].id),
        models.Restaurant(name="The Tandoor House", pin_code="110001", status="active", restaurant_fee=30.0, owner_id=users[1].id),
        models.Restaurant(name="Pasta Palace", pin_code="110002", status="active", restaurant_fee=20.0, owner_id=users[2].id),
        models.Restaurant(name="Dragon Wok", pin_code="110002", status="active", restaurant_fee=35.0, owner_id=users[2].id),
    ]
    db.add_all(restaurants)
    db.commit()
    for r in restaurants:
        db.refresh(r)

    print(f"✓ Created {len(restaurants)} restaurants")

    # ── Dishes ───────────────────────────────────────
    dishes = [
        # Spice Garden (restaurant 1)
        models.Dish(name="Butter Chicken", price=280.0, image_path="https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=400", availability=True, restaurant_id=restaurants[0].id),
        models.Dish(name="Paneer Tikka", price=220.0, image_path="https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=400", availability=True, restaurant_id=restaurants[0].id),
        models.Dish(name="Dal Makhani", price=180.0, image_path="https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400", availability=True, restaurant_id=restaurants[0].id),
        models.Dish(name="Garlic Naan", price=45.0, image_path="https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400", availability=True, restaurant_id=restaurants[0].id),
        models.Dish(name="Biryani", price=250.0, image_path="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400", availability=True, restaurant_id=restaurants[0].id),
        models.Dish(name="Gulab Jamun", price=80.0, image_path="https://images.unsplash.com/photo-1666190440370-fbf1e5f042d5?w=400", availability=False, restaurant_id=restaurants[0].id),

        # The Tandoor House (restaurant 2)
        models.Dish(name="Tandoori Chicken", price=320.0, image_path="https://images.unsplash.com/photo-1610057099431-d73a1c9d2f2f?w=400", availability=True, restaurant_id=restaurants[1].id),
        models.Dish(name="Seekh Kebab", price=240.0, image_path="https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400", availability=True, restaurant_id=restaurants[1].id),
        models.Dish(name="Chicken Tikka", price=260.0, image_path="https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400", availability=True, restaurant_id=restaurants[1].id),
        models.Dish(name="Rumali Roti", price=35.0, image_path="https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400", availability=True, restaurant_id=restaurants[1].id),

        # Pasta Palace (restaurant 3)
        models.Dish(name="Spaghetti Carbonara", price=350.0, image_path="https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400", availability=True, restaurant_id=restaurants[2].id),
        models.Dish(name="Margherita Pizza", price=299.0, image_path="https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400", availability=True, restaurant_id=restaurants[2].id),
        models.Dish(name="Caesar Salad", price=180.0, image_path="https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400", availability=True, restaurant_id=restaurants[2].id),
        models.Dish(name="Garlic Bread", price=120.0, image_path="https://images.unsplash.com/photo-1619535860434-ba1d8fa12536?w=400", availability=True, restaurant_id=restaurants[2].id),
        models.Dish(name="Tiramisu", price=200.0, image_path="https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400", availability=False, restaurant_id=restaurants[2].id),

        # Dragon Wok (restaurant 4)
        models.Dish(name="Kung Pao Chicken", price=290.0, image_path="https://images.unsplash.com/photo-1525755662778-989d0524087e?w=400", availability=True, restaurant_id=restaurants[3].id),
        models.Dish(name="Fried Rice", price=200.0, image_path="https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400", availability=True, restaurant_id=restaurants[3].id),
        models.Dish(name="Spring Rolls", price=150.0, image_path="https://images.unsplash.com/photo-1539735257881-5cc07593b442?w=400", availability=True, restaurant_id=restaurants[3].id),
        models.Dish(name="Dim Sum", price=220.0, image_path="https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=400", availability=True, restaurant_id=restaurants[3].id),
    ]
    db.add_all(dishes)
    db.commit()
    print(f"✓ Created {len(dishes)} dishes")

    # ── Delivery Partners ────────────────────────────
    delivery_partners = [
        models.DeliveryPartner(user_id=users[5].id, availability=True, pin_code="110001"),
        models.DeliveryPartner(user_id=users[6].id, availability=True, pin_code="110002"),
    ]
    db.add_all(delivery_partners)
    db.commit()
    print(f"✓ Created {len(delivery_partners)} delivery partners")

    # ── Offers ───────────────────────────────────────
    offers = [
        models.Offer(description="Welcome Offer - 10% off on first order!", discount_percentage=10.0, minimum_order_value=200.0, applicable_type="platform", restaurant_id=None, active=True),
        models.Offer(description="Mega Deal - 15% off on orders above ₹500", discount_percentage=15.0, minimum_order_value=500.0, applicable_type="platform", restaurant_id=None, active=True),
        models.Offer(description="Spice Garden Special - 20% off!", discount_percentage=20.0, minimum_order_value=400.0, applicable_type="restaurant", restaurant_id=restaurants[0].id, active=True),
        models.Offer(description="Pasta Lovers - 12% off!", discount_percentage=12.0, minimum_order_value=300.0, applicable_type="restaurant", restaurant_id=restaurants[2].id, active=True),
    ]
    db.add_all(offers)
    db.commit()
    print(f"✓ Created {len(offers)} offers")

    print("\n" + "="*50)
    print("  SEED DATA LOADED SUCCESSFULLY!")
    print("="*50)
    print("\nTest Accounts:")
    print("-" * 50)
    print(f"{'Role':<18} {'Email':<28} {'Password'}")
    print("-" * 50)
    print(f"{'Admin':<18} {'admin@pindrop.com':<28} password123")
    print(f"{'Owner (110001)':<18} {'raj@restaurant.com':<28} password123")
    print(f"{'Owner (110002)':<18} {'priya@restaurant.com':<28} password123")
    print(f"{'Customer (110001)':<18} {'amit@customer.com':<28} password123")
    print(f"{'Customer (110002)':<18} {'neha@customer.com':<28} password123")
    print(f"{'Delivery (110001)':<18} {'suresh@delivery.com':<28} password123")
    print(f"{'Delivery (110002)':<18} {'ravi@delivery.com':<28} password123")
    print(f"{'Care':<18} {'anita@care.com':<28} password123")
    print("-" * 50)

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
    raise
finally:
    db.close()
