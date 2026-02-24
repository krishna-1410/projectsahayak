# 🍽️ PinDrop Eats — Online Food Ordering & Delivery Management System

A complete multi-role food delivery platform built with **FastAPI**, **SQLite**, and **HTML/CSS/JS**.

---

## 📁 Project Structure

```
pinDropEats/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py           # SQLAlchemy engine & session
│   ├── models.py             # ORM models (10 tables)
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── auth.py               # JWT auth, password hashing, role checking
│   ├── seed.py               # Sample data seeder
│   ├── requirements.txt      # Python dependencies
│   └── routers/
│       ├── admin.py           # Admin endpoints
│       ├── restaurant_owner.py # Restaurant owner endpoints
│       ├── customer.py        # Customer endpoints
│       ├── delivery.py        # Delivery partner endpoints
│       └── customer_care.py   # Customer care endpoints
├── frontend/
│   ├── index.html            # Login / Register page
│   ├── customer.html         # Customer dashboard
│   ├── admin.html            # Admin dashboard
│   ├── owner.html            # Restaurant owner dashboard
│   ├── delivery.html         # Delivery partner dashboard
│   ├── care.html             # Customer care dashboard
│   ├── css/style.css         # Complete design system
│   └── js/app.js             # API helpers, auth, shared utilities
└── README.md
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.9+
- pip

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Seed the Database

```bash
cd backend
python seed.py
```

This creates the SQLite database (`pindropeats.db`) with sample data.

### 3. Start the Server

```bash
cd backend
python main.py
```

Server runs at: **http://localhost:8000**

### 4. Open the Frontend

Open `frontend/index.html` in your browser (or serve it via a simple HTTP server):

```bash
cd frontend
python -m http.server 5500
```

Then visit: **http://localhost:5500**

### 5. API Documentation

FastAPI auto-generated docs at: **http://localhost:8000/docs**

---

## 👥 Test Accounts

| Role | Email | Password | PIN Code |
|------|-------|----------|----------|
| Admin | admin@pindrop.com | password123 | 110001 |
| Owner | raj@restaurant.com | password123 | 110001 |
| Owner | priya@restaurant.com | password123 | 110002 |
| Customer | amit@customer.com | password123 | 110001 |
| Customer | neha@customer.com | password123 | 110002 |
| Delivery | suresh@delivery.com | password123 | 110001 |
| Delivery | ravi@delivery.com | password123 | 110002 |
| Care | anita@care.com | password123 | 110001 |

---

## 🔄 Order Lifecycle

```
Placed → Accepted → Preparing → Out for Delivery → Delivered
  │          │          │
  └→ Rejected (by owner)
  └→ Cancelled (by customer care at any stage before Delivered)
```

**Strict transition rules enforced:**
- Restaurant owner: Placed → Accepted/Rejected, Accepted → Preparing, Preparing → Out for Delivery
- Delivery partner: Out for Delivery → Delivered
- Customer care: Cancel any order not yet Delivered/Cancelled/Rejected
- No status can be skipped

---

## 📋 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Get current user |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/restaurants` | List all restaurants |
| POST | `/api/admin/restaurants` | Add restaurant |
| PUT | `/api/admin/restaurants/{id}` | Update restaurant |
| GET | `/api/admin/offers` | List platform offers |
| POST | `/api/admin/offers` | Create platform offer |
| DELETE | `/api/admin/offers/{id}` | Delete offer |
| GET | `/api/admin/stats` | Platform statistics |

### Restaurant Owner
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/owner/restaurant` | Get my restaurant |
| GET | `/api/owner/dishes` | List my dishes |
| POST | `/api/owner/dishes` | Add dish |
| PUT | `/api/owner/dishes/{id}` | Update dish |
| DELETE | `/api/owner/dishes/{id}` | Remove dish |
| GET | `/api/owner/orders` | List restaurant orders |
| PUT | `/api/owner/orders/{id}/status` | Update order status |
| GET | `/api/owner/offers` | List restaurant offers |
| POST | `/api/owner/offers` | Create restaurant offer |

### Customer
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/customer/restaurants` | Browse restaurants (by PIN) |
| GET | `/api/customer/restaurants/{id}/menu` | View menu |
| GET | `/api/customer/cart` | View cart |
| POST | `/api/customer/cart` | Add to cart |
| DELETE | `/api/customer/cart/{id}` | Remove cart item |
| DELETE | `/api/customer/cart` | Clear cart |
| GET | `/api/customer/offers` | Get eligible offers |
| POST | `/api/customer/checkout` | Place order |
| GET | `/api/customer/orders` | Order history |
| GET | `/api/customer/orders/{id}` | Order details |
| POST | `/api/customer/orders/{id}/reorder` | Reorder past order |
| POST | `/api/customer/complaints` | Raise complaint |
| GET | `/api/customer/complaints` | My complaints |

### Delivery Partner
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/delivery/status` | My status |
| PUT | `/api/delivery/availability` | Toggle availability |
| GET | `/api/delivery/orders` | My deliveries |
| PUT | `/api/delivery/orders/{id}/deliver` | Mark delivered |

### Customer Care
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/care/complaints` | All complaints |
| PUT | `/api/care/complaints/{id}` | Update complaint |
| GET | `/api/care/orders` | All orders |
| PUT | `/api/care/orders/{id}/cancel` | Cancel order |

### Shared
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | Get notifications |
| PUT | `/api/notifications/read` | Mark all as read |

---

## 🗃️ Database Schema

**10 Tables** with proper foreign keys:

1. **users** — All platform users (admin, owner, customer, delivery, care)
2. **restaurants** — Restaurant details with owner linkage
3. **dishes** — Menu items with images and availability
4. **delivery_partners** — Delivery partner profiles with availability status
5. **orders** — Order records with full lifecycle tracking
6. **order_items** — Individual items in each order
7. **offers** — Platform-level and restaurant-level offers
8. **complaints** — Customer complaints with resolution tracking
9. **cart** — Persistent shopping cart per customer
10. **notifications** — In-app notification system

---

## ⚙️ Business Rules Enforced

1. ✅ Customers only see restaurants matching their PIN code
2. ✅ Cannot add unavailable dishes to cart
3. ✅ Offers apply only when minimum order value is met
4. ✅ Order total = subtotal + restaurant fee − discount
5. ✅ Delivery partner assigned only if available and in same PIN code
6. ✅ Strict order status transitions (no skipping)
7. ✅ Cart restricted to one restaurant at a time
8. ✅ Proper JWT authentication with role-based access control
9. ✅ Input validation via Pydantic schemas
10. ✅ Passwords hashed with bcrypt

---

## 💡 Innovation Features

### 1. Delivery Time Estimation
Estimated delivery time calculated at checkout: `base 25 min + 2 min per item ± randomness`
Displayed on order tracking with visual timeline.

### 2. Reorder from Past Orders
One-click reorder button on order history — adds all available items back to cart.

### 3. Real-time Notification System
In-app notifications triggered on:
- Order status changes (customer gets notified)
- New order received (restaurant owner gets notified)
- Delivery assigned (delivery partner gets notified)
- Complaint updates (customer gets notified)

Notification bell with unread count in the navbar, auto-refreshes every 15 seconds.

---

## 🎨 Frontend Features

- **Responsive UI** with card-based layouts
- **Tab-based dashboards** for each role
- **Visual order timeline** showing progress through statuses
- **Toast notifications** for user feedback
- **Offer eligibility checking** with real-time total calculation
- **Clean, modern design** with orange + blue color scheme

---

## 🔄 Demo Flow

1. **Register** as customer (PIN: 110001) → Redirected to customer dashboard
2. **Browse** restaurants in your area → Click on a restaurant
3. **View menu** with dish images → Add items to cart
4. **View cart** → Apply an eligible offer → Place order
5. **Login as owner** (raj@restaurant.com) → See new order → Accept → Preparing → Out for Delivery
6. **Login as delivery** (suresh@delivery.com) → See assigned order → Mark as Delivered
7. **Login as customer** → Check order history → Raise complaint
8. **Login as care** (anita@care.com) → View complaint → Update status → Add resolution
9. **Login as admin** → View statistics → Manage restaurants and offers
