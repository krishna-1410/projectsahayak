# PinDrop Eats — Working Demo Guide & Technical Documentation

**Complete Walkthrough + Code Explanation + Module Interaction Reference**

---

## Table of Contents

1. [Setup & Launch](#1-setup--launch)
2. [Working Demo: Step-by-Step Flow](#2-working-demo-step-by-step-flow)
3. [Module Architecture Overview](#3-module-architecture-overview)
4. [Module 1: Database Layer (database.py)](#4-module-1-database-layer)
5. [Module 2: ORM Models (models.py)](#5-module-2-orm-models)
6. [Module 3: Pydantic Schemas (schemas.py)](#6-module-3-pydantic-schemas)
7. [Module 4: Authentication & Authorization (auth.py)](#7-module-4-authentication--authorization)
8. [Module 5: Application Entry Point (main.py)](#8-module-5-application-entry-point)
9. [Module 6: Admin Router (routers/admin.py)](#9-module-6-admin-router)
10. [Module 7: Restaurant Owner Router (routers/restaurant_owner.py)](#10-module-7-restaurant-owner-router)
11. [Module 8: Customer Router (routers/customer.py)](#11-module-8-customer-router)
12. [Module 9: Delivery Partner Router (routers/delivery.py)](#12-module-9-delivery-partner-router)
13. [Module 10: Customer Care Router (routers/customer_care.py)](#13-module-10-customer-care-router)
14. [Module 11: Seed Data Script (seed.py)](#14-module-11-seed-data-script)
15. [Module 12: Frontend Shared Utilities (js/app.js)](#15-module-12-frontend-shared-utilities)
16. [Module 13: Login Page (index.html)](#16-module-13-login-page)
17. [Module 14: Customer Dashboard (customer.html)](#17-module-14-customer-dashboard)
18. [Module 15: Admin Dashboard (admin.html)](#18-module-15-admin-dashboard)
19. [Module 16: Owner Dashboard (owner.html)](#19-module-16-owner-dashboard)
20. [Module 17: Delivery Dashboard (delivery.html)](#20-module-17-delivery-dashboard)
21. [Module 18: Customer Care Dashboard (care.html)](#21-module-18-customer-care-dashboard)
22. [Inter-Module Interaction Diagrams](#22-inter-module-interaction-diagrams)
23. [Business Rules Cross-Reference](#23-business-rules-cross-reference)

---

## 1. Setup & Launch

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```
This installs: FastAPI, uvicorn, SQLAlchemy, python-jose (JWT), passlib (password hashing), pydantic.

### Step 2: Seed the Database
```bash
cd backend
python seed.py
```
Creates `pindropeats.db` with 8 users, 4 restaurants, 19 dishes, 2 delivery partners, 4 offers.

### Step 3: Start Backend Server
```bash
cd backend
python main.py
```
Runs on **http://localhost:8000**. API docs at **http://localhost:8000/docs**

### Step 4: Start Frontend Server (separate terminal)
```bash
cd frontend
python -m http.server 5500
```
Runs on **http://localhost:5500**

### Step 5: Open Browser
Go to **http://localhost:5500** → You'll see the login page.

---

## 2. Working Demo: Step-by-Step Flow

### PHASE 1: ADMIN — Platform Setup

**Login:** `admin@pindrop.com` / `password123`

#### Demo Action 1.1: View Platform Statistics
1. After login, you land on the **📊 Statistics** tab
2. You see 4 dashboard cards: **Total Orders**, **Total Revenue**, **Total Restaurants**, **Total Customers**
3. Below that, **Orders by Status** shows how many orders are in each state

**What happens behind the scenes:**
- Frontend calls `GET /api/admin/stats`
- Backend (`routers/admin.py` → `get_platform_stats()`) runs COUNT and SUM queries on the orders, users, restaurants, and delivery_partners tables
- Returns aggregated data as JSON
- Frontend renders it as stat cards

#### Demo Action 1.2: Add a New Restaurant
1. Click the **🏪 Restaurants** tab
2. You see a table of all restaurants (Spice Garden, The Tandoor House, Pasta Palace, Dragon Wok)
3. Click **"+ Add Restaurant"** button
4. Fill in:
   - **Name:** "Biryani Blues"
   - **PIN Code:** "110001"
   - **Restaurant Fee:** 20
   - **Owner ID:** 9 (if Rakesh exists, or leave empty)
5. Click **"Save"** → Toast: "Restaurant added!"
6. The table refreshes and shows the new restaurant

**What happens behind the scenes:**
- Frontend calls `POST /api/admin/restaurants` with `{name, pin_code, restaurant_fee, owner_id}`
- Backend validates via Pydantic `RestaurantCreate` schema
- Creates a new row in the `restaurants` table
- Returns the created restaurant as JSON

#### Demo Action 1.3: Edit a Restaurant (Assign Owner, Toggle Status)
1. In the Restaurants table, click **"Edit"** on any restaurant
2. A form opens showing: Name, PIN Code, Fee, **Owner ID**, Status dropdown
3. Change the **Owner ID** to assign a different owner (e.g., enter `9` for Rakesh)
4. Change **Status** to "inactive" to disable a restaurant
5. Click **"Save Changes"** → Toast: "Restaurant updated!"

**What happens behind the scenes:**
- Frontend calls `PUT /api/admin/restaurants/{id}` with updated fields
- Backend uses `model_dump(exclude_unset=True)` — only updates fields that were sent
- The `owner_id` field links the restaurant to a user with role "owner"
- If status is set to "inactive", customers will no longer see this restaurant (PIN-based filter also checks `status = 'active'`)

#### Demo Action 1.4: Create Platform Offer
1. Click the **🎁 Platform Offers** tab
2. You see existing platform offers (Welcome Offer 10%, Mega Deal 15%)
3. Click **"+ Add Offer"**
4. Fill in:
   - **Description:** "Flash Sale - 25% off!"
   - **Discount (%):** 25
   - **Min Order Value (₹):** 600
5. Click **"Save"** → Offer appears in the table

**What happens behind the scenes:**
- Frontend calls `POST /api/admin/offers` with `{description, discount_percentage, minimum_order_value, applicable_type: "platform"}`
- Backend validates `applicable_type == "platform"` (admin cannot create restaurant-level offers)
- Creates row in `offers` table with `restaurant_id = NULL` and `applicable_type = "platform"`
- Platform offers are visible to ALL customers, regardless of which restaurant they order from

#### Demo Action 1.5: Delete Offer
1. Click **"Delete"** button on any offer → Confirm dialog
2. Offer is removed from the table

**What happens behind the scenes:**
- Frontend calls `DELETE /api/admin/offers/{id}`
- Backend deletes the row from the `offers` table

**Click Logout (top-right)**

---

### PHASE 2: RESTAURANT OWNER — Menu & Offer Setup

**Login:** `raj@restaurant.com` / `password123` (PIN: 110001, owns Spice Garden & The Tandoor House)

#### Demo Action 2.1: View Orders Tab
1. You land on the **📦 Orders** tab
2. Shows all orders for your restaurant(s) — initially may be empty or show past orders
3. Each order card shows: Order ID, Customer Name, Items, Total, Status with action buttons

**What happens behind the scenes:**
- Frontend calls `GET /api/owner/orders`
- Backend first finds which restaurant is linked to this owner (`_get_owner_restaurant()` checks `restaurants.owner_id == user.id`)
- Then queries `orders` table filtered by `restaurant_id`
- Joins with `order_items`, `dishes`, and `users` to build full response with dish names and customer names

#### Demo Action 2.2: Manage Dishes (Add, Toggle, Delete)
1. Click **🍽️ Dishes** tab
2. You see dish cards: Butter Chicken ₹280, Paneer Tikka ₹220, Dal Makhani ₹180, etc.
3. **Add a dish:** Click "+ Add Dish" → Fill name ("Chicken Biryani"), price (260), image URL (optional) → Click "Add"
4. **Toggle availability:** Click "Toggle" on "Gulab Jamun" (currently unavailable) → It becomes available
5. **Delete a dish:** Click "Delete" on any dish → It's removed

**What happens behind the scenes:**
- `POST /api/owner/dishes` → Backend validates `data.restaurant_id == rest.id` (owner can only add to their own restaurant), creates row in `dishes` table
- `PUT /api/owner/dishes/{id}` → Updates `availability` field. When set to false, customers see "Unavailable" and cannot add to cart
- `DELETE /api/owner/dishes/{id}` → Removes from `dishes` table

#### Demo Action 2.3: Create Restaurant-Level Offer
1. Click **🎁 Offers** tab
2. You see the "Spice Garden Special - 20% off!" offer
3. Click "+ Add Offer" → Description: "Lunch Special 10%", Discount: 10, Min: 200 → Save

**What happens behind the scenes:**
- Frontend calls `POST /api/owner/offers` with `{applicable_type: "restaurant"}`
- Backend forces `offer.restaurant_id = rest.id` (owner's restaurant)
- This offer will ONLY show for customers ordering from this specific restaurant

**Click Logout**

---

### PHASE 3: CUSTOMER — Browse, Order, Track, Complain

**Login:** `amit@customer.com` / `password123` (PIN: 110001)

#### Demo Action 3.1: Browse Restaurants
1. You land on the **🏪 Restaurants** tab
2. You see ONLY restaurants in PIN 110001: "Spice Garden" and "The Tandoor House"
3. You do NOT see "Pasta Palace" or "Dragon Wok" (they are in PIN 110002)
4. Click on **"Spice Garden"**

**What happens behind the scenes:**
- Frontend calls `GET /api/customer/restaurants`
- Backend filters: `WHERE restaurant.pin_code == user.pin_code AND status == 'active'`
- Only restaurants matching customer's PIN code (110001) are returned
- Frontend renders them as clickable cards

#### Demo Action 3.2: View Menu & Add to Cart
1. You're now on the **📋 Menu** tab showing Spice Garden's dishes
2. You see: Butter Chicken ₹280, Paneer Tikka ₹220, Dal Makhani ₹180, Garlic Naan ₹45, Biryani ₹250
3. "Gulab Jamun" shows as **"Currently Unavailable"** with a disabled button
4. Click **"+ Add to Cart"** on Butter Chicken → Toast: "Added to cart!"
5. Click **"+ Add to Cart"** on Dal Makhani (click twice to get quantity 2)
6. Notice the **Cart badge** in the tab bar updates: "Cart (3)"

**What happens behind the scenes (Add to Cart):**
- Frontend calls `POST /api/customer/cart` with `{dish_id: X, quantity: 1}`
- Backend (`routers/customer.py` → `add_to_cart()`) does 5 checks:
  1. Dish exists? (404 if not)
  2. Dish available? (400 if not — "This dish is currently unavailable")
  3. Restaurant in user's PIN code? (403 if not)
  4. Cart already has items from a DIFFERENT restaurant? (400 — "You can only order from one restaurant at a time. Clear your cart first.")
  5. Dish already in cart? → If yes, increment `quantity` instead of creating new row
- Creates/updates row in `cart` table

**DEMO: Try the single-restaurant rule!**
- Go back to Restaurants → Click "The Tandoor House" → Try adding "Tandoori Chicken"
- You'll get error: **"You can only order from one restaurant at a time. Clear your cart first."**
- This proves the business rule is working!

#### Demo Action 3.3: Cart, Offers & Checkout
1. Click the **🛒 Cart** tab
2. You see:
   - Butter Chicken ₹280 × 1 = ₹280
   - Dal Makhani ₹180 × 2 = ₹360
   - **Subtotal: ₹640.00**
3. Under "Apply Offer", the dropdown shows eligible offers:
   - "Welcome Offer - 10% off on first order!" (min ₹200) ✅
   - "Mega Deal - 15% off on orders above ₹500" (min ₹500) ✅
   - "Spice Garden Special - 20% off!" (min ₹400) ✅
4. Select **"Spice Garden Special - 20% off!"**
5. The display updates:
   - Subtotal: ₹640.00
   - Restaurant Fee: ₹25.00
   - Discount: -₹128.00 (20% of ₹640)
   - **Total: ₹537.00**
6. Select **Payment Mode:** "Online Payment"
7. Click **"Place Order"**
8. Toast: **"Order #1 placed successfully! Est. delivery: 31 min"**
9. You're automatically switched to the Orders tab

**What happens behind the scenes (Checkout):**
- Frontend calls `POST /api/customer/checkout` with `{payment_mode: "online", offer_id: 3}`
- Backend (`routers/customer.py` → `checkout()`) does:
  1. Loads all cart items for this customer
  2. Re-validates every dish is still available (prevents stale cart)
  3. Calculates subtotal: `Σ(dish.price × quantity)`
  4. Validates offer: checks `offer.active == True`, minimum order value met, offer belongs to correct restaurant (for restaurant offers)
  5. Calculates discount: `subtotal × (discount_percentage / 100)`
  6. Calculates total: `subtotal + restaurant_fee - discount`
  7. Estimates delivery time: `25 + (total_items × 2) + random(-5, +5)`, minimum 15 min
  8. Creates `Order` record in DB (status: "Placed")
  9. Creates `OrderItem` records for each cart item (stores price snapshot)
  10. Deletes all cart items for this customer
  11. Sends notification to restaurant owner: "New order #1 received!"

#### Demo Action 3.4: View Order with Timeline
1. On the **📦 My Orders** tab, you see your new order
2. The **order timeline** shows: Placed (active) → Accepted → Preparing → Out for Delivery → Delivered
3. You see: estimated delivery time, item breakdown, discount applied, total, payment mode
4. Two buttons: **"🔄 Reorder"** and **"💬 Raise Complaint"**

**What happens behind the scenes:**
- Frontend calls `GET /api/customer/orders`
- Backend joins orders with order_items, dishes, restaurants, delivery_partners
- Returns full order data including delivery_partner_name (null at this point)
- Frontend's `renderTimeline()` function builds a 5-step visual progress bar

#### Demo Action 3.5: Check Notification Bell
1. Click the **🔔** bell icon in the navbar
2. You don't have notifications yet (owner hasn't acted yet)
3. After the owner processes the order, notifications will appear here

**Don't logout yet! Open a new browser tab or incognito window for the next steps.**

---

### PHASE 4: RESTAURANT OWNER — Process the Order

**Login (new tab):** `raj@restaurant.com` / `password123`

#### Demo Action 4.1: See Notification
1. The **🔔 bell** shows a red badge with "1"
2. Click the bell → Notification: "New order #1 received!"

**What happens behind the scenes:**
- The `create_notification()` helper was called during checkout
- Frontend polls `GET /api/notifications` every 15 seconds (via `setInterval(loadNotifications, 15000)`)
- Shows unread count on bell badge

#### Demo Action 4.2: Accept the Order
1. On the **📦 Orders** tab, you see Order #1 with status "Placed"
2. Two buttons appear: **"Accept"** and **"Reject"**
3. Click **"Accept"**
4. Toast: "Order status updated to 'Accepted'"
5. The order card now shows status "Accepted" with a **"Preparing"** button

**What happens behind the scenes:**
- Frontend calls `PUT /api/owner/orders/1/status` with `{status: "Accepted"}`
- Backend checks transition map: `VALID_OWNER_TRANSITIONS = {"Placed": ["Accepted", "Rejected"], ...}`
- "Placed" → "Accepted" is allowed ✅
- Updates `orders.order_status` to "Accepted"
- Calls `create_notification(db, order.customer_id, "Order #1 status updated to: Accepted")`
- Customer's bell will show this notification

#### Demo Action 4.3: Start Preparing
1. Click **"Preparing"** button
2. Toast: "Order status updated to 'Preparing'"
3. Now a **"Out for Delivery"** button appears

**What happens behind the scenes:**
- Transition "Accepted" → "Preparing" is valid ✅
- Customer gets notification: "Order #1 status updated to: Preparing"

#### Demo Action 4.4: Send Out for Delivery
1. Click **"Out for Delivery"**
2. Toast: "Order status updated to 'Out for Delivery'"

**THIS IS WHERE THE MAGIC HAPPENS — What happens behind the scenes:**
- Backend checks transition: "Preparing" → "Out for Delivery" ✅
- **Delivery Partner Auto-Assignment Logic:**
  ```
  1. Query: SELECT * FROM delivery_partners 
     WHERE availability = TRUE AND pin_code = '110001'
  2. Finds Suresh (DP ID:1, available, PIN 110001)
  3. Sets order.delivery_partner_id = 1
  4. Sets Suresh's availability = FALSE (he's now busy)
  5. Notification to Suresh: "New delivery assigned! Order #1"
  6. Notification to customer: "Order #1 status updated to: Out for Delivery"
  ```
- **If no delivery partner is available:** The transition is BLOCKED with error: "No delivery partner available in this area. Cannot send for delivery."

**Switch to customer's browser tab → Check bell → You'll see multiple notifications!**

---

### PHASE 5: DELIVERY PARTNER — Deliver the Order

**Login (new tab):** `suresh@delivery.com` / `password123`

#### Demo Action 5.1: Check Status
1. On the **🟢 My Status** tab, you see a large **🔴** icon
2. Status shows: **OFFLINE** (because the system set availability to FALSE when assigning the order)
3. Your name and PIN code are displayed

**What happens behind the scenes:**
- Frontend calls `GET /api/delivery/status`
- Backend finds the DeliveryPartner record linked to this user
- Returns availability, pin_code, and name

#### Demo Action 5.2: Check Notification
1. Click **🔔** bell → "New delivery assigned! Order #1"

#### Demo Action 5.3: View Assigned Order
1. Click **📦 My Deliveries** tab
2. You see Order #1 with:
   - Restaurant name, Customer name, Items list, Total amount, Payment mode
   - Status: "Out for Delivery"
   - A big green **"✅ Mark as Delivered"** button

**What happens behind the scenes:**
- Frontend calls `GET /api/delivery/orders`
- Backend filters: `WHERE orders.delivery_partner_id == partner.id`
- Joins with restaurant and customer tables for names

#### Demo Action 5.4: Mark as Delivered
1. Click **"✅ Mark as Delivered"**
2. Toast: "Order delivered successfully"
3. The button disappears — order now shows status "Delivered"
4. Go back to **🟢 My Status** → Status is now **🟢 AVAILABLE** again

**What happens behind the scenes:**
- Frontend calls `PUT /api/delivery/orders/1/deliver`
- Backend validates: current status must be "Out for Delivery" (any other status → error)
- Sets `order.order_status = "Delivered"`
- Sets `partner.availability = True` (free for next assignment)
- Notification to customer: "Order #1 has been delivered! Enjoy your meal! 🍽️"

---

### PHASE 6: CUSTOMER — Post-Delivery Actions

**Switch back to customer's browser tab**

#### Demo Action 6.1: See Delivered Order
1. Click **📦 My Orders** tab → Refresh
2. Order #1 now shows **"Delivered"** status
3. The timeline shows all 5 dots completed (green with ✓ marks)
4. Delivery partner name is now visible (Suresh Yadav)

#### Demo Action 6.2: Reorder (Innovation Feature)
1. Click **"🔄 Reorder"** on the delivered order
2. Toast: "Reorder complete. 2 items added to cart, 0 unavailable items skipped."
3. Click **🛒 Cart** tab → All items from the old order are back in the cart!

**What happens behind the scenes:**
- Frontend calls `POST /api/customer/orders/1/reorder`
- Backend (`reorder()` function):
  1. Finds the original order and its items
  2. Clears current cart
  3. For each item in the old order: checks if dish still exists and is available
  4. If available → creates new `Cart` row with same dish and quantity
  5. If unavailable → skips it and counts as "skipped"
  6. Returns count of added vs skipped items

#### Demo Action 6.3: Raise a Complaint
1. Click **💬 Complaints** tab
2. Under "Raise a Complaint":
   - Select Order: **"#1 — Spice Garden (Delivered)"**
   - Description: "Food was cold when delivered"
3. Click **"Submit Complaint"**
4. Toast: "Complaint submitted!"
5. The complaint appears in the table below with status: **"Open"**

**What happens behind the scenes:**
- Frontend calls `POST /api/customer/complaints` with `{order_id: 1, description: "..."}`
- Backend validates that the order belongs to this customer
- Creates row in `complaints` table with `status: "Open"`, `resolution_notes: NULL`
- The complaint is now visible to Customer Care executives

---

### PHASE 7: CUSTOMER CARE — Handle Complaint & Cancel Orders

**Login (new tab):** `anita@care.com` / `password123`

#### Demo Action 7.1: View All Complaints
1. You land on the **💬 Complaints** tab
2. You see the complaint from Amit:
   - Complaint #1 — Order #1
   - Customer: Amit Singh
   - Description: "Food was cold when delivered"
   - Status: **Open**

#### Demo Action 7.2: Update Complaint Status
1. In the **Update Status** dropdown, select **"In Progress"**
2. In **Resolution Notes**, type: "Investigating with restaurant. Will refund if needed."
3. Click **"Update Complaint"**
4. Toast: "Complaint updated!"
5. The complaint card now shows "In Progress" badge and resolution notes

**What happens behind the scenes:**
- Frontend calls `PUT /api/care/complaints/1` with `{status: "In Progress", resolution_notes: "..."}`
- Backend validates status is one of: Open, In Progress, Resolved, Closed
- Updates the `complaints` table
- Notification to customer: "Complaint #1 updated to: In Progress"

#### Demo Action 7.3: Resolve Complaint
1. Change status to **"Resolved"**
2. Update resolution notes: "Refund of ₹100 issued. Restaurant warned."
3. Click **"Update Complaint"**
4. Customer will see this resolution on their Complaints tab

#### Demo Action 7.4: View All Orders
1. Click the **📦 All Orders** tab
2. You see a table of ALL orders across the platform
3. Orders that can be cancelled show a red **"Cancel"** button
4. Delivered/Cancelled/Rejected orders show "-" (cannot be cancelled)

#### Demo Action 7.5: Cancel an Order
1. First, have a customer place a new order (go back to customer tab → use the items in cart → checkout)
2. Return to Care dashboard → All Orders tab
3. Find the new order (status: "Placed") → Click **"Cancel"**
4. Confirm dialog → Click OK
5. Toast: "Order #2 cancelled successfully"

**What happens behind the scenes:**
- Frontend calls `PUT /api/care/orders/2/cancel`
- Backend checks: status NOT in ["Delivered", "Cancelled", "Rejected"]
- Sets `order.order_status = "Cancelled"`
- If a delivery partner was assigned: sets `partner.availability = True` (frees them)
- Notification to customer: "Order #2 has been cancelled by customer care."

---

### PHASE 8: ADMIN — Verify Final Statistics

**Login:** `admin@pindrop.com` / `password123`

1. Click **📊 Statistics** tab
2. Total Orders should now show **2** (or more)
3. Total Revenue shows the sum of all order totals
4. Orders by Status shows: Delivered: 1, Cancelled: 1 (etc.)
5. This proves the entire lifecycle worked from creation to completion

---

### BONUS DEMO: Multiple Delivery Partners

1. **As Customer:** Place 2 orders from Spice Garden (one at a time)
2. **As Owner (Raj):** Accept both → Preparing both → "Out for Delivery" on Order #1
   - Suresh gets assigned (becomes unavailable)
3. **"Out for Delivery" on Order #2:**
   - Krishna gets assigned (he was the second available partner in PIN 110001)
4. **Try "Out for Delivery" on a 3rd order:**
   - ERROR: "No delivery partner available in this area" ← Both partners busy!
5. **As Suresh:** Mark Order #1 delivered → Suresh becomes available again
6. **As Owner:** Retry "Out for Delivery" on Order #3 → Now Suresh gets assigned ✅

---

## 3. Module Architecture Overview

```
┌──────────────────────── FRONTEND (Browser) ────────────────────────────┐
│                                                                        │
│  index.html ──→ Login/Register forms                                   │
│     ↓ (after login, redirects to role-specific page)                  │
│  customer.html ──→ 5 tabs (Restaurants, Menu, Cart, Orders, Complain) │
│  admin.html    ──→ 3 tabs (Stats, Restaurants, Offers)                │
│  owner.html    ──→ 3 tabs (Orders, Dishes, Offers)                    │
│  delivery.html ──→ 2 tabs (Status, Deliveries)                        │
│  care.html     ──→ 2 tabs (Complaints, All Orders)                    │
│                                                                        │
│  All pages load: css/style.css (design system) + js/app.js (shared)   │
│  js/app.js provides: API client, auth, toast, tabs, timeline, navbar  │
│                                                                        │
└───────────────────────────── HTTP REST + JWT ──────────────────────────┘
                                    │
                                    ▼
┌──────────────────────── BACKEND (FastAPI) ─────────────────────────────┐
│                                                                        │
│  main.py ──→ App creation, CORS, Auth endpoints, Notification APIs    │
│     ↓ (includes routers)                                              │
│  routers/admin.py            ─ /api/admin/*    ─ requires role=admin  │
│  routers/restaurant_owner.py ─ /api/owner/*    ─ requires role=owner  │
│  routers/customer.py         ─ /api/customer/* ─ requires role=customer│
│  routers/delivery.py         ─ /api/delivery/* ─ requires role=delivery│
│  routers/customer_care.py    ─ /api/care/*     ─ requires role=care   │
│                                                                        │
│  auth.py    ──→ JWT creation/verification, password hashing, role dep │
│  schemas.py ──→ Pydantic models for request/response validation       │
│  models.py  ──→ SQLAlchemy ORM models (10 tables)                     │
│  database.py──→ SQLAlchemy engine, session factory, base class        │
│                                                                        │
└───────────────────────────── SQLAlchemy ORM ───────────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────┐
                         │  SQLite Database  │
                         │ pindropeats.db   │
                         │  (10 tables)     │
                         └──────────────────┘
```

### How a Request Flows Through Modules

```
1. User clicks a button in frontend (e.g., "Place Order")
         ↓
2. js/app.js → apiPost('/api/customer/checkout', {...})
   Adds JWT token to Authorization header
         ↓
3. HTTP request hits FastAPI (main.py)
   → CORS middleware allows it
   → Routes to customer.py router based on URL prefix /api/customer/*
         ↓
4. Router function signature has Depends():
   - Depends(get_db)         → database.py provides a DB session
   - Depends(require_role()) → auth.py extracts JWT, verifies it,
                                loads User from DB, checks role
         ↓
5. Business logic executes:
   - Reads/writes via models.py (SQLAlchemy ORM)
   - Validates I/O via schemas.py (Pydantic)
   - Calls create_notification() from auth.py for events
         ↓
6. Returns JSON response → js/app.js parses it → Frontend updates UI
```

---

## 4. Module 1: Database Layer

**File:** `backend/database.py`

### What It Does
Establishes the connection between Python and the SQLite database file.

### Code Explanation

```python
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'pindropeats.db')}"
```
- Constructs the SQLite connection string pointing to `pindropeats.db` in the backend folder.

```python
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```
- `create_engine` creates the SQLAlchemy database engine — the core interface to the DB.
- `check_same_thread=False` is needed for SQLite because FastAPI uses multiple threads, while SQLite by default only allows access from the thread that created the connection.

```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```
- Creates a session factory. Each API request gets its own DB session (like a temporary workspace for queries).
- `autocommit=False` means we must explicitly call `db.commit()` to save changes.
- `autoflush=False` means SQL isn't sent on every object attribute change — only when we explicitly flush or commit.

```python
Base = declarative_base()
```
- Creates the base class that all ORM models inherit from. This connects model classes to actual database tables.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
- This is a **dependency generator**. FastAPI calls it before each request to provide a DB session, and guarantees the session is closed after the request (even if an error occurs).
- Used as `Depends(get_db)` in every router function.

### Who Uses This Module
- **models.py** — inherits from `Base` to define table classes
- **main.py** — calls `Base.metadata.create_all(bind=engine)` to create tables at startup
- **Every router** — uses `Depends(get_db)` to get a DB session
- **seed.py** — uses `SessionLocal()` to insert sample data

---

## 5. Module 2: ORM Models

**File:** `backend/models.py`

### What It Does
Defines 10 Python classes that map to 10 database tables. Each class attribute becomes a table column.

### Table-by-Table Explanation

#### User Model
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin, owner, customer, delivery, care
    pin_code = Column(String(10), nullable=False)
```
- `primary_key=True` — Auto-incrementing unique ID.
- `unique=True` on email — Prevents duplicate registration.
- `index=True` on email — Creates a database index for fast login lookups.
- `role` — Determines which dashboard the user sees and which APIs they can access.
- `pin_code` — Defines the user's service area for geographic filtering.

**Relationships:**
```python
orders = relationship("Order", back_populates="customer", foreign_keys="Order.customer_id")
notifications = relationship("Notification", back_populates="user")
complaints = relationship("Complaint", back_populates="customer")
cart_items = relationship("Cart", back_populates="customer")
```
- These define bidirectional links. `user.orders` gives all orders by this customer. `order.customer` gives the customer of an order.

#### Restaurant Model
```python
class Restaurant(Base):
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dishes = relationship("Dish", back_populates="restaurant", cascade="all, delete-orphan")
```
- `ForeignKey("users.id")` — Links restaurant to an owner user.
- `nullable=True` — Restaurant can exist without an owner initially (admin creates it first, assigns owner later).
- `cascade="all, delete-orphan"` — If a restaurant is deleted, all its dishes are automatically deleted too.

#### Dish Model
```python
class Dish(Base):
    availability = Column(Boolean, default=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
```
- `availability` — When False, customers cannot add this dish to cart. The frontend shows "Unavailable".
- Every dish MUST belong to a restaurant (`nullable=False`).

#### DeliveryPartner Model
```python
class DeliveryPartner(Base):
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    availability = Column(Boolean, default=True)
    pin_code = Column(String(10), nullable=False)
```
- `unique=True` on user_id — Each user can only have ONE delivery partner profile.
- `availability` — Set to False when assigned to an order, True when delivery is completed.
- `pin_code` — Must match the restaurant's PIN code for assignment to work.

#### Order Model
```python
class Order(Base):
    order_status = Column(String(30), default="Placed")
    delivery_partner_id = Column(Integer, ForeignKey("delivery_partners.id"), nullable=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)
    estimated_delivery_time = Column(Integer, nullable=True)
```
- `order_status` — The heart of the state machine: Placed → Accepted → Preparing → Out for Delivery → Delivered (or Rejected/Cancelled).
- `delivery_partner_id` — NULL until the order is sent "Out for Delivery", then populated with the auto-assigned partner.
- `offer_id` — Records which offer was applied (NULL if no offer).
- `estimated_delivery_time` — Calculated at checkout (in minutes).

#### OrderItem Model
```python
class OrderItem(Base):
    price = Column(Float, nullable=False)
```
- `price` stores the **snapshot** of the dish price at order time. Even if the restaurant later changes the dish price, the order retains the original price.

#### Offer Model
```python
class Offer(Base):
    applicable_type = Column(String(20), nullable=False)  # platform, restaurant
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
```
- `applicable_type = "platform"` → Available to ALL customers, `restaurant_id = NULL`.
- `applicable_type = "restaurant"` → Only for orders from that specific restaurant.

#### Complaint Model
```python
class Complaint(Base):
    status = Column(String(30), default="Open")  # Open, In Progress, Resolved, Closed
    resolution_notes = Column(Text, nullable=True)
```
- Customer Care updates `status` through the workflow.
- `resolution_notes` — Text explanation from Care executive.

#### Cart Model
```python
class Cart(Base):
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
```
- Stores `restaurant_id` alongside the dish — this enables the **single-restaurant constraint**. When adding to cart, the backend checks if the new dish's restaurant matches the existing cart items' restaurant.

#### Notification Model
```python
class Notification(Base):
    is_read = Column(Boolean, default=False)
```
- `is_read` — When user opens notification dropdown, all are marked as read. Unread count shows on the bell badge.

### How Models Interact
```
User ←──── owns ────→ Restaurant ←──── has ────→ Dish
  │                       │                         │
  ├── places ──→ Order ←── from ───┘                │
  │               │                                 │
  │               ├── contains ──→ OrderItem ←── references
  │               │
  │               ├── assigned to ──→ DeliveryPartner ←── is a ──→ User
  │               │
  │               └── uses ──→ Offer ←── belongs to ──→ Restaurant
  │
  ├── files ──→ Complaint ←── about ──→ Order
  ├── has ──→ Cart ←── contains ──→ Dish
  └── receives ──→ Notification
```

---

## 6. Module 3: Pydantic Schemas

**File:** `backend/schemas.py`

### What It Does
Defines the **shape** of every API request and response. Pydantic validates incoming data (type checking, required fields, custom rules) and serializes outgoing data.

### Key Schema Groups

#### Auth Schemas
```python
class UserCreate(BaseModel):
    @field_validator("role")
    def validate_role(cls, v):
        allowed = ["admin", "owner", "customer", "delivery", "care"]
        if v not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v
```
- The `@field_validator` decorator runs automatically when the API receives registration data.
- If someone tries to register with `role: "superuser"`, Pydantic raises a 422 Unprocessable Entity error BEFORE the router function even runs.

#### Restaurant Schemas
```python
class RestaurantUpdate(BaseModel):
    name: Optional[str] = None        # Optional — only sent fields are updated
    owner_id: Optional[int] = None    # Admin sets this to link an owner
```
- All fields are `Optional` — `model_dump(exclude_unset=True)` in the router returns only the fields the client actually sent, so the update only modifies those fields.

#### Order Schemas
```python
class OrderResponse(BaseModel):
    items: List[OrderItemResponse] = []
    restaurant_name: Optional[str] = None
    delivery_partner_name: Optional[str] = None
    class Config:
        from_attributes = True
```
- `from_attributes = True` allows Pydantic to read data from SQLAlchemy model attributes (instead of requiring a dict).
- `restaurant_name` and `delivery_partner_name` are NOT database columns — they're populated manually in the router by joining related tables.

#### Offer Schemas
```python
class OfferCreate(BaseModel):
    @field_validator("discount_percentage")
    def validate_discount(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        return v
```
- Ensures no one can create a 0% or 150% discount.

### Request → Schema → Router Flow
```
Client sends JSON: {"email": "test@test.com", "password": "abc"}
    ↓
Pydantic (UserCreate) validates:
    - email: ✅ string
    - password: ❌ "Password must be at least 6 characters" → 422 Error
    ↓ (if valid)
Router function receives a validated UserCreate object
```

---

## 7. Module 4: Authentication & Authorization

**File:** `backend/auth.py`

### What It Does
Handles: password hashing, JWT token creation/verification, user extraction from token, role-based access control, and a notification helper.

### Code Explanation

#### Password Hashing
```python
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
```
- Uses PBKDF2-SHA256 hashing (industry standard, one-way).
- `hash_password("password123")` → `"$pbkdf2-sha256$29000$..."` (irreversible).
- `verify_password("password123", hashed)` → True/False (compares without decrypting).

#### JWT Token Creation
```python
def create_access_token(data: dict, ...):
    to_encode = data.copy()  # {"user_id": 5, "role": "customer"}
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```
- Creates a token containing `user_id`, `role`, and 24-hour expiry.
- Signed with `SECRET_KEY` — if anyone tampers with the token, verification fails.
- The token is sent to the frontend after login/register, stored in `localStorage`.

#### Token Verification
```python
def decode_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload  # {"user_id": 5, "role": "customer", "exp": 1740500000}
```
- Verifies signature and expiry. If invalid or expired → 401 Unauthorized.

#### Get Current User (FastAPI Dependency)
```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("user_id")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user
```
- `Depends(security)` extracts the Bearer token from the `Authorization: Bearer <token>` header.
- Decodes the token to get `user_id`.
- Loads the full User object from the database.
- This is the ** core dependency** — almost every API endpoint uses it.

#### Role Checker (Dependency Factory)
```python
def require_role(*roles):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Access denied...")
        return current_user
    return role_checker
```
- **This is a function that returns a function** (a factory pattern).
- Usage: `user = Depends(require_role("admin"))` → Only admin users pass through. Anyone else gets 403 Forbidden.
- Can accept multiple roles: `require_role("admin", "care")`.

#### Notification Helper
```python
def create_notification(db, user_id, message):
    notif = models.Notification(user_id=user_id, message=message)
    db.add(notif)
    db.commit()
```
- Simple helper called by routers wherever events happen (order status changes, delivery assigned, complaint updated, etc.).

### Auth Flow Diagram
```
Frontend: POST /api/auth/login {email, password}
    ↓
main.py → login():
    1. Find user by email
    2. verify_password(plain, hashed) → True?
    3. create_access_token({user_id, role})
    4. Return {access_token, user}
    ↓
Frontend: stores token in localStorage
    ↓
Frontend: GET /api/customer/restaurants
    Headers: Authorization: Bearer eyJ...
    ↓
auth.py → get_current_user():
    1. Extract token from Authorization header
    2. decode_token() → {user_id: 4, role: "customer"}
    3. Load User from DB
    ↓
auth.py → require_role("customer"):
    4. user.role == "customer"? ✅
    ↓
customer.py → browse_restaurants(user=<User object>):
    5. Use user.pin_code to filter restaurants
```

---

## 8. Module 5: Application Entry Point

**File:** `backend/main.py`

### What It Does
Creates the FastAPI application, configures middleware, includes all routers, and defines auth + notification endpoints.

### Code Explanation

#### App Creation & CORS
```python
app = FastAPI(title="PinDrop Eats", ...)
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```
- CORS (Cross-Origin Resource Sharing) middleware is REQUIRED because the frontend runs on `localhost:5500` while the backend runs on `localhost:8000`. Without CORS, the browser would block all API calls.
- `allow_origins=["*"]` allows requests from any origin (for development).

#### Router Inclusion
```python
app.include_router(admin.router)          # /api/admin/*
app.include_router(restaurant_owner.router) # /api/owner/*
app.include_router(customer.router)        # /api/customer/*
app.include_router(delivery.router)        # /api/delivery/*
app.include_router(customer_care.router)   # /api/care/*
```
- Each router handles a different URL prefix.
- FastAPI automatically generates Swagger docs combining all routers at `/docs`.

#### Registration Endpoint — Delivery Partner Auto-Creation
```python
if data.role == "delivery":
    dp = models.DeliveryPartner(
        user_id=user.id, availability=True, pin_code=data.pin_code
    )
    db.add(dp)
    db.commit()
```
- When a delivery partner registers, the system automatically creates their `delivery_partners` record.
- This is why registration through the frontend works seamlessly — the partner can immediately see their status dashboard.

#### Notification Endpoints
```python
@app.get("/api/notifications")    # Fetch last 20 notifications
@app.put("/api/notifications/read")  # Mark all as read
```
- These are NOT role-restricted — any authenticated user can access their own notifications.
- Filtered by `user.id` so users only see their own notifications.

---

## 9. Module 6: Admin Router

**File:** `backend/routers/admin.py`

### What It Does
Provides 3 feature groups: Restaurant Management, Platform Offer Management, Platform Statistics.

### Technical Details

#### Restaurant CRUD
- **List:** Returns ALL restaurants (no PIN filter — admin sees everything).
- **Create:** Accepts `name, pin_code, restaurant_fee, owner_id`. Owner ID can be NULL (unassigned).
- **Update:** Uses `model_dump(exclude_unset=True)` — a partial update pattern. Only modifies fields included in the request.

#### Platform Statistics
```python
total_revenue = db.query(func.coalesce(func.sum(models.Order.total_amount), 0)).scalar()
status_counts = db.query(models.Order.order_status, func.count(models.Order.id)).group_by(...).all()
```
- `func.coalesce(sum, 0)` — Returns 0 instead of NULL when there are no orders.
- `GROUP BY order_status` — Counts orders in each status for the breakdown chart.

### Module Interactions
```
admin.py ——→ models.py (Restaurant, Offer, Order, User, DeliveryPartner)
admin.py ——→ schemas.py (RestaurantCreate, RestaurantUpdate, OfferCreate, PlatformStats)
admin.py ——→ auth.py (require_role("admin"))
admin.py ——→ database.py (get_db)
```

---

## 10. Module 7: Restaurant Owner Router

**File:** `backend/routers/restaurant_owner.py`

### What It Does
Manages dishes, processes orders through the state machine, and handles restaurant-level offers.

### Key Technical Detail: State Machine

```python
VALID_OWNER_TRANSITIONS = {
    "Placed": ["Accepted", "Rejected"],
    "Accepted": ["Preparing"],
    "Preparing": ["Out for Delivery"],
}
```
- This dictionary IS the state machine. Every status update is validated against it.
- Example: If order is in "Placed" status, only "Accepted" or "Rejected" are allowed. Any other value → 400 error.

### Key Technical Detail: Delivery Partner Auto-Assignment

```python
if new_status == "Out for Delivery":
    partner = db.query(models.DeliveryPartner).filter(
        models.DeliveryPartner.availability == True,
        models.DeliveryPartner.pin_code == rest.pin_code,
    ).first()
    if not partner:
        raise HTTPException(status_code=400, detail="No delivery partner available...")
    order.delivery_partner_id = partner.id
    partner.availability = False
```
- `.first()` returns the first matching partner — this is the "first available, first assigned" strategy.
- If multiple partners are available, the one with the lowest database ID gets assigned.
- `partner.availability = False` prevents double-assignment.

### Key Technical Detail: Owner-Restaurant Linkage

```python
def _get_owner_restaurant(db, user):
    rest = db.query(models.Restaurant).filter(models.Restaurant.owner_id == user.id).first()
    if not rest:
        raise HTTPException(status_code=404, detail="No restaurant linked to your account")
    return rest
```
- Every owner action first finds their restaurant. If no restaurant is linked → 404.
- This is why Rakesh gets "No restaurant linked" until an admin assigns a restaurant to him.

### Module Interactions
```
restaurant_owner.py ——→ models.py (Restaurant, Dish, Order, OrderItem, DeliveryPartner, Offer)
restaurant_owner.py ——→ auth.py (require_role("owner"), create_notification())
restaurant_owner.py ——→ schemas.py (DishCreate, DishUpdate, OrderStatusUpdate, OfferCreate)
```

---

## 11. Module 8: Customer Router

**File:** `backend/routers/customer.py`

### What It Does
The most feature-rich router — handles restaurant browsing, cart management, offer application, checkout, order history, reorder, and complaints.

### Key Technical Detail: PIN Code Filtering

```python
def browse_restaurants(user):
    return db.query(models.Restaurant).filter(
        models.Restaurant.pin_code == user.pin_code,
        models.Restaurant.status == "active",
    ).all()
```
- The JWT token contains the user_id → backend loads the full User object → uses `user.pin_code` for filtering.
- Customers CANNOT see restaurants outside their area — this is enforced at the API level, not just the frontend.

### Key Technical Detail: Cart Single-Restaurant Constraint

```python
existing_cart = db.query(models.Cart).filter(models.Cart.customer_id == user.id).first()
if existing_cart and existing_cart.restaurant_id != dish.restaurant_id:
    raise HTTPException(status_code=400, detail="You can only order from one restaurant at a time...")
```
- Before adding any item, checks if the cart already has items from a different restaurant.
- Forces customer to clear cart before switching restaurants.

### Key Technical Detail: Checkout Price Calculation

```python
# 1. Calculate subtotal
for ci in cart_items:
    item_total = dish.price * ci.quantity
    subtotal += item_total

# 2. Apply offer discount
if data.offer_id:
    if subtotal < offer.minimum_order_value:
        raise HTTPException(...)  # Minimum not met
    discount = subtotal * (offer.discount_percentage / 100)

# 3. Calculate total
total = subtotal + restaurant_fee - discount

# 4. Estimate delivery time
estimated_time = 25 + (total_items * 2) + random.randint(-5, 5)
estimated_time = max(estimated_time, 15)  # Minimum 15 min
```
- Price snapshot: Each OrderItem stores `price` at checkout time, not a reference to current dish price.
- Delivery time formula: Base 25 minutes + 2 minutes per item ± random variance, minimum 15 minutes.

### Key Technical Detail: Reorder Feature

```python
def reorder(order_id, user):
    db.query(models.Cart).filter(models.Cart.customer_id == user.id).delete()  # Clear cart
    for item in old_order.items:
        if dish and dish.availability:
            db.add(Cart(customer_id=user.id, dish_id=dish.id, quantity=item.quantity, ...))
            added += 1
        else:
            skipped += 1
```
- Clears existing cart first.
- Copies each item from the old order into the cart.
- Skips unavailable dishes (they may have been disabled since the original order).
- Reports back how many items were added vs skipped.

### Module Interactions
```
customer.py ——→ models.py (Restaurant, Dish, Cart, Order, OrderItem, Offer, Complaint, Notification)
customer.py ——→ auth.py (require_role("customer"), create_notification())
customer.py ——→ schemas.py (CartAdd, CheckoutRequest, ComplaintCreate, etc.)
customer.py ——→ Python's random module (delivery time estimation)
```

---

## 12. Module 9: Delivery Partner Router

**File:** `backend/routers/delivery.py`

### What It Does
3 simple functions: get status, toggle availability, view assigned orders, mark delivered.

### Key Technical Detail: Toggle Availability

```python
def toggle_availability(user):
    partner = _get_partner(db, user)
    partner.availability = not partner.availability  # Boolean flip
    db.commit()
```
- Simple boolean toggle. When offline, the partner won't be assigned to new orders.
- When the system assigns an order, it ALSO sets availability to False automatically.

### Key Technical Detail: Mark Delivered

```python
def mark_delivered(order_id, user):
    if order.order_status != "Out for Delivery":
        raise HTTPException(...)  # Can only deliver from "Out for Delivery"
    order.order_status = "Delivered"
    partner.availability = True  # Free up for next delivery
```
- Strict check: can only deliver orders currently "Out for Delivery".
- Automatically frees the partner — they appear as available for the next order assignment.
- Sends notification to customer: "Order delivered! Enjoy your meal! 🍽️"

### Module Interactions
```
delivery.py ——→ models.py (DeliveryPartner, Order, OrderItem)
delivery.py ——→ auth.py (require_role("delivery"), create_notification())
delivery.py ——→ schemas.py (DeliveryPartnerResponse, OrderResponse)
```

---

## 13. Module 10: Customer Care Router

**File:** `backend/routers/customer_care.py`

### What It Does
Manages complaints workflow and provides order cancellation power.

### Key Technical Detail: Complaint Workflow

```python
allowed_statuses = ["Open", "In Progress", "Resolved", "Closed"]
if data.status not in allowed_statuses:
    raise HTTPException(...)
complaint.status = data.status
complaint.resolution_notes = data.resolution_notes
```
- Status must be one of the 4 allowed values.
- Resolution notes are optional — care executive adds them as they work the complaint.
- Notification sent to customer on every update.

### Key Technical Detail: Order Cancellation with Partner Release

```python
def cancel_order(order_id):
    non_cancellable = ["Delivered", "Cancelled", "Rejected"]
    if order.order_status in non_cancellable:
        raise HTTPException(...)
    order.order_status = "Cancelled"
    if order.delivery_partner_id:
        partner.availability = True  # Free the delivery partner
```
- Cannot cancel orders that are already Delivered, Cancelled, or Rejected.
- CAN cancel at any other stage (Placed, Accepted, Preparing, Out for Delivery).
- If a delivery partner was assigned, they are freed automatically.

### Module Interactions
```
customer_care.py ——→ models.py (Complaint, Order, DeliveryPartner, User)
customer_care.py ——→ auth.py (require_role("care"), create_notification())
customer_care.py ——→ schemas.py (ComplaintResponse, ComplaintUpdate, OrderResponse)
```

---

## 14. Module 11: Seed Data Script

**File:** `backend/seed.py`

### What It Does
Populates the database with realistic sample data for demonstration.

### How It Works
1. `Base.metadata.drop_all(bind=engine)` — Deletes ALL existing tables (fresh start).
2. `Base.metadata.create_all(bind=engine)` — Recreates all 10 tables (empty).
3. Inserts data in dependency order:
   - Users first (no foreign key dependencies)
   - Restaurants second (needs user IDs for owner_id)
   - Dishes third (needs restaurant IDs)
   - Delivery Partners (needs user IDs)
   - Offers (needs restaurant IDs)

### Seed Data Summary

| Entity | Count | Details |
|--------|-------|---------|
| Users | 8 | 1 admin, 2 owners, 2 customers, 2 delivery, 1 care |
| Restaurants | 4 | Spice Garden, Tandoor House (PIN 110001), Pasta Palace, Dragon Wok (PIN 110002) |
| Dishes | 19 | 6 + 4 + 5 + 4 per restaurant. 2 marked unavailable. |
| Delivery Partners | 2 | 1 per PIN code (110001, 110002) |
| Offers | 4 | 2 platform-wide, 2 restaurant-specific |

### PIN Code Geography
```
PIN 110001                    PIN 110002
├── Spice Garden              ├── Pasta Palace
├── The Tandoor House         ├── Dragon Wok
├── Customer: Amit            ├── Customer: Neha
├── Delivery: Suresh          ├── Delivery: Ravi
├── Owner: Raj                └── Owner: Priya
├── Admin
└── Care: Anita
```
- Amit can ONLY see Spice Garden and Tandoor House.
- Neha can ONLY see Pasta Palace and Dragon Wok.
- Suresh delivers ONLY in 110001. Ravi delivers ONLY in 110002.

---

## 15. Module 12: Frontend Shared Utilities

**File:** `frontend/js/app.js`

### What It Does
Provides shared JavaScript functions used by ALL 6 HTML pages.

### Key Functions Explained

#### API Client
```javascript
const API_BASE = 'http://localhost:8000';

async function api(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const resp = await fetch(url, { ...options, headers });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);
    return data;
}
```
- Every API call goes through this function.
- Automatically attaches the JWT token from `localStorage`.
- Parses JSON response and throws an error if status is not 2xx.
- If token is expired (401), automatically calls `logout()` which redirects to login page.

Convenience wrappers:
- `apiGet(endpoint)` — GET request
- `apiPost(endpoint, body)` — POST with JSON body
- `apiPut(endpoint, body)` — PUT with optional JSON body
- `apiDelete(endpoint)` — DELETE request

#### Auth Helpers
```javascript
function saveAuth(data) {
    localStorage.setItem('pde_token', data.access_token);
    localStorage.setItem('pde_user', JSON.stringify(data.user));
}

function requireAuth(role) {
    const user = getUser();
    if (!user || !getToken()) { window.location.href = 'index.html'; return null; }
    if (role && user.role !== role) { window.location.href = getDashboardUrl(user.role); return null; }
    return user;
}
```
- After login/register, token and user data are stored in browser's `localStorage` (persists across page refreshes).
- Each dashboard page calls `requireAuth('rolename')` at the top. If no token → redirect to login. If wrong role → redirect to correct dashboard.

#### Toast Notifications
```javascript
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;  // 'success', 'error', 'info'
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);  // Auto-dismiss after 4 seconds
}
```
- Creates a floating notification element.
- Green for success, red for error.
- Automatically removes itself after 4 seconds.

#### Tab System
```javascript
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Deactivate all tabs & content panels
            // Activate clicked tab & matching panel
            if (window.tabCallbacks && window.tabCallbacks[target]) {
                window.tabCallbacks[target]();  // Load data for the tab
            }
        });
    });
}
```
- Each dashboard defines `window.tabCallbacks` mapping tab IDs to load functions.
- When a tab is clicked, the corresponding load function is called (lazy loading — data is fetched only when the tab is opened).

#### Order Timeline
```javascript
function renderTimeline(currentStatus) {
    const steps = ['Placed', 'Accepted', 'Preparing', 'Out for Delivery', 'Delivered'];
    steps.forEach((step, i) => {
        if (i < currentIdx) cls = 'completed';      // Green with ✓
        else if (i === currentIdx) cls = 'active';   // Orange highlight
        else cls = '';                                // Gray (not reached)
    });
}
```
- Creates a 5-step visual progress bar.
- Completed steps show green checkmarks.
- Current step is highlighted.
- If order is Cancelled/Rejected, only the first step shows as completed, and a red badge appears below.

#### Notification Bell
```javascript
setInterval(loadNotifications, 15000);  // Poll every 15 seconds
```
- Every 15 seconds, the frontend calls `GET /api/notifications` to check for new notifications.
- Updates the unread count badge on the bell icon.
- When user clicks the bell, dropdown opens and `PUT /api/notifications/read` marks all as read.

---

## 16. Module 13: Login Page

**File:** `frontend/index.html`

### What It Does
Registration and login forms with automatic role-based redirect.

### How Login Works
```
User types email + password → clicks "Login"
    ↓
handleLogin() calls apiPost('/api/auth/login', {email, password})
    ↓
Backend verifies credentials → returns {access_token, user: {id, name, email, role, pin_code}}
    ↓
saveAuth(data) stores token + user in localStorage
    ↓
getDashboardUrl(user.role) → redirects to:
  admin    → admin.html
  owner    → owner.html
  customer → customer.html
  delivery → delivery.html
  care     → care.html
```

### How Registration Works
```
User fills: name, email, password, role (dropdown), PIN code → clicks "Register"
    ↓
handleRegister() calls apiPost('/api/auth/register', {...})
    ↓
Backend:
  1. Check email not already registered
  2. Hash password (PBKDF2-SHA256)
  3. Create User record
  4. If role == "delivery" → auto-create DeliveryPartner record
  5. Generate JWT token
  6. Return token + user
    ↓
Same redirect as login
```

### Auto-Redirect Logic
```javascript
const user = getUser();
if (user && getToken()) {
    window.location.href = getDashboardUrl(user.role);
}
```
- If user is already logged in (token exists in localStorage), they're immediately redirected to their dashboard. They never see the login form again until they logout.

---

## 17. Module 14: Customer Dashboard

**File:** `frontend/customer.html`

### Tabs and Their Functions

#### Tab 1: Restaurants
- Calls `apiGet('/api/customer/restaurants')`.
- Renders restaurant cards in a 3-column grid.
- Each card shows: first letter as banner, restaurant name, PIN code, fee.
- Clicking a card calls `viewMenu(id, name)` → stores `selectedRestaurant` object → switches to Menu tab.

#### Tab 2: Menu
- Calls `apiGet('/api/customer/restaurants/${id}/menu')`.
- Renders dish cards with image (from Unsplash URL), name, price.
- Unavailable dishes show "Currently Unavailable" label and disabled button.
- "Add to Cart" button calls `addToCart(dishId)` → `apiPost('/api/customer/cart', {dish_id, quantity: 1})`.
- Cart badge updates via `updateCartBadge()` (counts total items in cart).

#### Tab 3: Cart
- Calls `apiGet('/api/customer/cart')` for items.
- Calls `apiGet('/api/customer/offers?restaurant_id=X')` for eligible offers.
- Calculates subtotal on the frontend.
- **Offer dropdown:** When selected, `updateTotal()` runs:
  - Checks if subtotal >= offer's minimum → shows "Applied!" or "Add ₹X more"
  - Calculates discount: `subtotal × (percentage / 100)`
  - Updates total display: `subtotal + fee - discount`
- **Checkout:** Calls `apiPost('/api/customer/checkout', {payment_mode, offer_id})`.
- On success, clears cart badge and switches to Orders tab.

#### Tab 4: Orders
- Calls `apiGet('/api/customer/orders')`.
- Each order card shows: ID, date, status badge, restaurant name, delivery partner name, estimated time.
- `renderTimeline(status)` draws the 5-step progress bar.
- Items list with prices, discount line, fee line, total.
- **Reorder button:** `apiPost('/api/customer/orders/${id}/reorder')` → switches to Cart tab.
- **Raise Complaint button:** Switches to Complaints tab with order pre-selected.

#### Tab 5: Complaints
- Loads both `apiGet('/api/customer/complaints')` and `apiGet('/api/customer/orders')`.
- Form: Order dropdown + Description textarea + Submit button.
- Table: Shows complaint ID, order, description, status badge, resolution notes, date.

---

## 18. Module 15: Admin Dashboard

**File:** `frontend/admin.html`

### Tabs and Their Functions

#### Tab 1: Statistics
- Calls `apiGet('/api/admin/stats')`.
- 4 stat cards in a grid: Total Orders, Total Revenue, Restaurants, Customers.
- Orders by Status section: Shows status badges with counts.

#### Tab 2: Restaurants
- Calls `apiGet('/api/admin/restaurants')`.
- Table with columns: ID, Name, PIN, Status, Fee, Owner ID, Actions.
- **Add Restaurant form:** Name, PIN, Fee, Owner ID inputs.
- **Edit button:** Opens an inline form with ALL editable fields (Name, PIN, Fee, Owner ID, Status dropdown). This is how you assign an owner to a restaurant.

#### Tab 3: Platform Offers
- Calls `apiGet('/api/admin/offers')`.
- Table: ID, Description, Discount %, Min Value, Delete button.
- **Add Offer form:** Description, Discount %, Min Order Value. Type is forced to "platform".

---

## 19. Module 16: Owner Dashboard

**File:** `frontend/owner.html`

### Tabs and Their Functions

#### Tab 1: Orders
- First loads restaurant info via `apiGet('/api/owner/restaurant')`.
- Then calls `apiGet('/api/owner/orders')`.
- Each order card shows customer name, items, total, status.
- Action buttons change based on status:
  - **Placed:** "Accept" and "Reject" buttons
  - **Accepted:** "Preparing" button
  - **Preparing:** "Out for Delivery" button
  - **Delivered/Cancelled etc.:** No action buttons
- Clicking a button calls `apiPut('/api/owner/orders/${id}/status', {status: "..."})`.

#### Tab 2: Dishes
- Calls `apiGet('/api/owner/dishes')`.
- Dish cards with image, name, price, availability badge.
- **Add Dish form:** Name, Price, Image URL, restaurant_id (auto-filled).
- **Toggle button:** Flips availability via `apiPut('/api/owner/dishes/${id}', {availability: !current})`.
- **Delete button:** Calls `apiDelete('/api/owner/dishes/${id}')`.

#### Tab 3: Offers
- Calls `apiGet('/api/owner/offers')`.
- Shows restaurant-specific offers.
- **Add Offer form:** Description, Discount %, Min Order Value. Type forced to "restaurant".

---

## 20. Module 17: Delivery Dashboard

**File:** `frontend/delivery.html`

### Tabs and Their Functions

#### Tab 1: My Status
- Calls `apiGet('/api/delivery/status')`.
- Large emoji: 🟢 (available) or 🔴 (offline).
- Shows name, PIN code, status badge.
- Toggle button: Calls `apiPut('/api/delivery/availability')` → flips availability.

#### Tab 2: My Deliveries
- Calls `apiGet('/api/delivery/orders')`.
- Shows orders assigned to this partner.
- Each card: Order ID, date, restaurant name, customer name, items, total, payment mode.
- **"✅ Mark as Delivered"** button appears ONLY for orders in "Out for Delivery" status.
- Clicking it calls `apiPut('/api/delivery/orders/${id}/deliver')`.
- After delivery, refreshes both the orders list and the status page (partner becomes available again).

---

## 21. Module 18: Customer Care Dashboard

**File:** `frontend/care.html`

### Tabs and Their Functions

#### Tab 1: Complaints
- Calls `apiGet('/api/care/complaints')`.
- Each complaint card shows:
  - Complaint ID, Order ID, Customer name, Date
  - Description in a highlighted box
  - Resolution notes (if any)
  - **Status dropdown:** Open → In Progress → Resolved → Closed
  - **Resolution Notes input field**
  - **"Update Complaint" button:** Calls `apiPut('/api/care/complaints/${id}', {status, resolution_notes})`
  - **"Cancel Order" button:** (for active orders) Calls `apiPut('/api/care/orders/${order_id}/cancel')`

#### Tab 2: All Orders
- Calls `apiGet('/api/care/orders')`.
- Table: ID, Customer, Restaurant, Total, Status, Date, Actions.
- Active orders show a **"Cancel"** button.
- Orders that are Delivered/Cancelled/Rejected show "-" (cannot be cancelled).

### Pre-loading Pattern
```javascript
apiGet('/api/care/orders').then(o => ordersCache = o).catch(() => {});
```
- When the page loads, orders are fetched into `ordersCache` so the Complaints tab can check order statuses to decide whether to show the "Cancel Order" button.

---

## 22. Inter-Module Interaction Diagrams

### Interaction 1: Customer Places Order → Owner Gets Notified

```
Customer Dashboard (customer.html)
    └──→ apiPost('/api/customer/checkout')
              │
              ▼
         customer.py → checkout()
              │
              ├── Reads: Cart, Dish, Restaurant, Offer
              ├── Writes: Order, OrderItem
              ├── Deletes: Cart items
              │
              └── create_notification(owner_id, "New order received!")
                      │
                      ▼
                 models.py → Notification row created
                      │
                      ▼
         Owner Dashboard (owner.html)
              └── loadNotifications() [every 15 sec via app.js]
                   └── apiGet('/api/notifications')
                        └── Shows bell badge with count
```

### Interaction 2: Owner Sends for Delivery → Partner Auto-Assigned

```
Owner Dashboard (owner.html)
    └──→ apiPut('/api/owner/orders/1/status', {status: "Out for Delivery"})
              │
              ▼
         restaurant_owner.py → update_order_status()
              │
              ├── Validates: "Preparing" → "Out for Delivery" ✅
              │
              ├── Query: SELECT * FROM delivery_partners
              │         WHERE availability=TRUE AND pin_code='110001'
              │
              ├── Sets: order.delivery_partner_id = partner.id
              ├── Sets: partner.availability = FALSE
              │
              ├── create_notification(partner.user_id, "Delivery assigned!")
              └── create_notification(customer_id, "Order out for delivery!")
                      │
                      ▼
         Delivery Dashboard (delivery.html)
              └── loadNotifications() detects new notification
              └── loadOrders() shows the assigned order
         Customer Dashboard (customer.html)
              └── loadOrders() shows updated timeline
```

### Interaction 3: Partner Delivers → All Parties Updated

```
Delivery Dashboard (delivery.html)
    └──→ apiPut('/api/delivery/orders/1/deliver')
              │
              ▼
         delivery.py → mark_delivered()
              │
              ├── Sets: order.order_status = "Delivered"
              ├── Sets: partner.availability = TRUE
              │
              └── create_notification(customer_id, "Order delivered! 🍽️")
                      │
                      ▼
         Customer Dashboard: timeline shows all 5 steps complete
         Owner Dashboard: order card shows "Delivered" badge
         Admin Dashboard: stats update (Delivered count +1)
         Delivery Dashboard: partner status back to 🟢 AVAILABLE
```

### Interaction 4: Customer Complains → Care Resolves

```
Customer Dashboard (customer.html)
    └──→ apiPost('/api/customer/complaints', {order_id, description})
              │
              ▼
         customer.py → raise_complaint()
              └── Creates Complaint row (status: "Open")
                      │
                      ▼
         Care Dashboard (care.html)
              └── loadComplaints() shows new complaint
              └── apiPut('/api/care/complaints/1', {status: "Resolved", resolution_notes: "..."})
                      │
                      ▼
                 customer_care.py → update_complaint()
                      ├── Updates complaint status + notes
                      └── create_notification(customer_id, "Complaint updated!")
                              │
                              ▼
                 Customer Dashboard: complaint table shows "Resolved" + resolution notes
                 Customer notification bell: "Complaint #1 updated to: Resolved"
```

### Interaction 5: Care Cancels Order → Partner Freed

```
Care Dashboard (care.html)
    └──→ apiPut('/api/care/orders/2/cancel')
              │
              ▼
         customer_care.py → cancel_order()
              │
              ├── Sets: order.order_status = "Cancelled"
              ├── If partner assigned: partner.availability = TRUE
              └── create_notification(customer_id, "Order cancelled by care")
                      │
                      ▼
         Customer: sees Cancelled status on order
         Delivery Partner: now available for new assignments
         Admin: stats show updated Cancelled count
```

---

## 23. Business Rules Cross-Reference

| Business Rule | Backend Enforcement | Frontend Enforcement |
|---|---|---|
| **PIN code filtering** | customer.py → `WHERE pin_code == user.pin_code` | Shows "Restaurants near you (PIN: X)" |
| **Unavailable dishes blocked** | customer.py → `if not dish.availability: raise 400` | Disabled "Add to Cart" button |
| **Single-restaurant cart** | customer.py → checks `existing_cart.restaurant_id != dish.restaurant_id` | Error toast: "Clear your cart first" |
| **Minimum offer value** | customer.py (checkout) → `if subtotal < min: raise 400` | Warning: "Add ₹X more" in cart |
| **Price formula** | customer.py → `total = subtotal + fee - discount` | Cart shows itemized breakdown |
| **Strict order transitions** | restaurant_owner.py → `VALID_OWNER_TRANSITIONS` dict | Buttons only shown for valid transitions |
| **No status skipping** | All routers validate current → new transition | Timeline UI shows sequential progress |
| **Delivery partner = same PIN** | restaurant_owner.py → `WHERE pin_code == rest.pin_code` | Error if no partner available |
| **Partner freed on delivery** | delivery.py → `partner.availability = True` | Status changes from 🔴 to 🟢 |
| **Partner freed on cancel** | customer_care.py → `partner.availability = True` | Partner can be assigned again |
| **JWT auth required** | auth.py → `get_current_user()` dependency on every endpoint | `requireAuth(role)` on every page |
| **Role-based access** | auth.py → `require_role()` returns 403 | Redirect to correct dashboard |
| **Password hashed** | auth.py → `pbkdf2_sha256` | Password field is type="password" |
| **Email unique** | models.py → `unique=True` on email column | Error message: "Email already registered" |

---

*Complete Technical Reference — PinDrop Eats*
*Date: February 24, 2026*
