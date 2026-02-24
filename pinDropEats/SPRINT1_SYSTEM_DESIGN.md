# Sprint 1 — System Design Document

**Project Name:** Online Food Ordering & Delivery Management System (PinDrop Eats)
**Sprint:** 1 — Foundation Design & Architecture Planning
**Date:** February 24, 2026
**Version:** 1.0

---

## Table of Contents

1. [Problem Understanding](#1-problem-understanding)
2. [Role Responsibilities](#2-role-responsibilities)
3. [Order Lifecycle Design](#3-order-lifecycle-design)
4. [System Architecture](#4-system-architecture)
5. [Database Schema Design](#5-database-schema-design)
6. [Entity Relationships Explanation](#6-entity-relationships-explanation)
7. [API Endpoint Planning](#7-api-endpoint-planning)
8. [UI Screen Planning](#8-ui-screen-planning)
9. [Business Rules Enforcement Strategy](#9-business-rules-enforcement-strategy)
10. [Assumptions Made](#10-assumptions-made)
11. [Task Allocation for Team of 3](#11-task-allocation-for-team-of-3)
12. [How This Design Satisfies Evaluation Criteria](#12-how-this-design-satisfies-evaluation-criteria)

---

## 1. Problem Understanding

### 1.1 What Problem Are We Solving?

Online food ordering has become a daily necessity, but building such a platform requires careful handling of multiple user roles, real-time order tracking, location-based filtering, and strict business rules. Our system — **PinDrop Eats** — addresses these challenges by creating a **multi-role, PIN-code-based food delivery platform** with a complete order lifecycle.

### 1.2 Core Problem Breakdown

| Problem Area | Description |
|---|---|
| **Multi-role access** | Five distinct user types (Admin, Restaurant Owner, Customer, Delivery Partner, Customer Care) each need different capabilities and restricted views. |
| **Location-based filtering** | Customers must only see restaurants and delivery options relevant to their geographic area, identified by PIN code. |
| **Order lifecycle management** | Orders pass through a strict sequence of states. No state can be skipped, and each transition can only be performed by the authorised role. |
| **Business rule enforcement** | Pricing calculations, offer eligibility, delivery partner assignment, and cart restrictions must all follow defined rules without exception. |
| **Complaint resolution** | Customers must be able to raise complaints, and a dedicated customer care team must manage them through a defined workflow. |

### 1.3 Key Stakeholders

- **Customers** — Order food and expect fast, transparent delivery.
- **Restaurant Owners** — Manage menus, receive orders, and update preparation status.
- **Delivery Partners** — Accept and fulfill deliveries in their service area.
- **Admin** — Oversees platform operations, manages restaurants, and configures offers.
- **Customer Care** — Handles disputes, resolves complaints, and can cancel orders.

### 1.4 Project Scope for Sprint 1

- Complete system design and database schema
- API endpoint planning for all five roles
- UI screen identification and layout planning
- Business rule formalization
- Architecture decision documentation

---

## 2. Role Responsibilities

### 2.1 Admin

| Responsibility | Description |
|---|---|
| Manage Restaurants | Add new restaurants, update existing ones (name, PIN code, status, fee, assign owner). |
| Configure Platform Offers | Create, view, and delete platform-wide discount offers that apply to all restaurants. |
| View Platform Statistics | Access dashboard with total orders, total revenue, restaurant count, customer count, delivery partner count, and order breakdown by status. |

**Access Level:** Full platform visibility. Cannot directly modify orders or complaints.

---

### 2.2 Restaurant Owner

| Responsibility | Description |
|---|---|
| Manage Menu (Dishes) | Add new dishes with name, price, image, and availability status. Update price and availability. Remove dishes. |
| Process Orders | View incoming orders. Accept or reject new orders. Update status from Accepted → Preparing → Out for Delivery. |
| Configure Restaurant Offers | Create discount offers specific to their restaurant with minimum order value conditions. |

**Access Level:** Restricted to their own restaurant's data only.

---

### 2.3 Customer

| Responsibility | Description |
|---|---|
| Register & Login | Create account with name, email, password, and PIN code. |
| Browse Restaurants | View only active restaurants matching their PIN code. |
| View Menu | See all dishes for a selected restaurant, including images, prices, and availability. |
| Manage Cart | Add available dishes to cart, remove items, clear cart. Cart is restricted to one restaurant at a time. |
| Apply Offers | View eligible offers (platform-wide + restaurant-specific). Apply an offer if minimum order value is met. |
| Checkout | Place order with payment mode selection. See price breakdown (subtotal + fee − discount). Receive estimated delivery time. |
| Track Orders | View order history with real-time status timeline. |
| Reorder | One-click reorder from past order history (innovation feature). |
| Raise Complaints | Submit complaints linked to specific orders. Track complaint resolution status. |
| Receive Notifications | Get in-app notifications on order status changes, delivery updates, and complaint resolutions. |

**Access Level:** Own data only. Cannot see other customers' orders or data.

---

### 2.4 Delivery Partner

| Responsibility | Description |
|---|---|
| Toggle Availability | Switch between available (online) and offline status. |
| View Assigned Orders | See list of orders assigned for delivery, including restaurant name, customer name, items, and order total. |
| Mark Delivered | Confirm delivery of an order. This frees the partner for the next assignment. |

**Access Level:** Only their own assignments. Auto-assigned by the system based on PIN code and availability.

---

### 2.5 Customer Care Executive

| Responsibility | Description |
|---|---|
| View All Complaints | See all customer complaints with order details, description, and current status. |
| Update Complaint Status | Change complaint status through workflow: Open → In Progress → Resolved → Closed. Add resolution notes. |
| Cancel Orders | Cancel any order that has not yet been Delivered, Cancelled, or Rejected. Cancellation frees assigned delivery partners. |
| View All Orders | Access all orders across the platform for reference during complaint handling. |

**Access Level:** Read access to all orders and complaints. Write access to complaint status and order cancellation.

---

## 3. Order Lifecycle Design

### 3.1 State Transition Diagram (Text-Based)

```
                              ┌─────────────┐
                              │   PLACED     │  ← Customer places order
                              └──────┬───────┘
                                     │
                          ┌──────────┼──────────┐
                          ▼                      ▼
                   ┌─────────────┐        ┌─────────────┐
                   │  ACCEPTED   │        │  REJECTED   │  ← Owner decides
                   └──────┬──────┘        └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  PREPARING  │  ← Owner starts cooking
                   └──────┬──────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  OUT FOR DELIVERY     │  ← Owner hands to delivery partner
              └───────────┬───────────┘    (auto-assigns available partner
                          │                 in same PIN code)
                          ▼
                   ┌─────────────┐
                   │  DELIVERED  │  ← Delivery partner confirms
                   └─────────────┘

              ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

              ┌─────────────┐
              │  CANCELLED  │  ← Customer Care can cancel at any stage
              └─────────────┘    before Delivered/Cancelled/Rejected
```

### 3.2 Transition Rules

| Current State | Allowed Next State(s) | Who Can Transition | Side Effects |
|---|---|---|---|
| **Placed** | Accepted, Rejected | Restaurant Owner | Customer is notified |
| **Accepted** | Preparing | Restaurant Owner | Customer is notified |
| **Preparing** | Out for Delivery | Restaurant Owner | Delivery partner auto-assigned from same PIN code; partner marked unavailable; both customer and partner notified |
| **Out for Delivery** | Delivered | Delivery Partner | Partner marked available again; customer notified |
| **Any (pre-delivery)** | Cancelled | Customer Care | Delivery partner (if assigned) freed; customer notified |

### 3.3 Key Constraint

> **No status can be skipped.** The system enforces that each transition is only valid from the immediately preceding state. For example, an order in "Accepted" state cannot jump directly to "Out for Delivery" — it must go through "Preparing" first.

### 3.4 Delivery Partner Assignment Logic

```
When Owner transitions order to "Out for Delivery":
    1. Query delivery_partners table
    2. Filter: availability = TRUE AND pin_code = restaurant's pin_code
    3. If found → assign first available partner to the order
                → set partner.availability = FALSE
                → send notification to partner
    4. If NOT found → BLOCK the transition
                    → return error: "No delivery partner available in this area"
```

---

## 4. System Architecture

### 4.1 High-Level Architecture (Text-Based Diagram)

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Browser)                        │
│                                                                  │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │
│  │ Customer  │ │  Owner   │ │  Admin   │ │ Delivery │ │ Care │ │
│  │ Dashboard │ │Dashboard │ │Dashboard │ │Dashboard │ │ Dash │ │
│  └─────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──┬───┘ │
│        │             │            │             │          │     │
│  ┌─────┴─────────────┴────────────┴─────────────┴──────────┴───┐ │
│  │              Shared JavaScript (app.js)                     │ │
│  │        API Client · Auth Manager · Toast Notifications      │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
└─────────────────────────────┼────────────────────────────────────┘
                              │  HTTP REST (JSON)
                              │  Authorization: Bearer <JWT>
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI Server)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   CORS Middleware                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────── Auth Layer ────────────────────────────┐  │
│  │  JWT Token Generation · Token Verification · Role Checker │  │
│  │  Password Hashing (PBKDF2-SHA256)                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────── Role-Based API Routers ───────────────────────┐  │
│  │                                                           │  │
│  │  /api/admin/*       →  Admin Router       (admin role)    │  │
│  │  /api/owner/*       →  Owner Router       (owner role)    │  │
│  │  /api/customer/*    →  Customer Router    (customer role) │  │
│  │  /api/delivery/*    →  Delivery Router    (delivery role) │  │
│  │  /api/care/*        →  Care Router        (care role)     │  │
│  │  /api/auth/*        →  Auth Endpoints     (public)        │  │
│  │  /api/notifications →  Notification Endpoints (any auth)  │  │
│  │                                                           │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │              ORM Layer (SQLAlchemy)                        │  │
│  │         Models · Relationships · Query Builder            │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │   SQLite Database  │
                    │  (pindropeats.db)  │
                    │    10 Tables       │
                    └────────────────────┘
```

### 4.2 Architecture Decisions

| Decision | Rationale |
|---|---|
| **FastAPI (Python)** | Modern, high-performance framework with built-in request validation (Pydantic), automatic API docs (Swagger), and async support. |
| **SQLite** | Zero-configuration embedded database. Ideal for development and demonstration. The SQLAlchemy ORM makes it easy to migrate to PostgreSQL/MySQL later. |
| **JWT Authentication** | Stateless, scalable authentication. Each token carries user_id and role, enabling role checks without database lookups per request. |
| **Role-based Router Separation** | Each role has its own router file with a dedicated URL prefix. This enforces clean separation of concerns and makes access control auditable. |
| **HTML + CSS + JS (No Framework)** | Simple, dependency-free frontend. Each role gets its own HTML page. Shared logic in a single JS utility file reduces duplication. |
| **Single-Server Deployment** | Backend serves both the API and static frontend files. Simplifies deployment for demonstration. |

### 4.3 Request Flow Example (Customer Places Order)

```
1. Customer clicks "Place Order" button
2. Frontend (app.js) sends POST /api/customer/checkout with JWT
3. CORS middleware allows the request
4. Auth middleware extracts JWT → verifies → loads User object
5. Role checker confirms user.role == "customer"
6. Customer router's checkout() function:
   a. Loads cart items from DB
   b. Validates all dishes are still available
   c. Validates offer eligibility (if applied)
   d. Calculates: total = subtotal + restaurant_fee − discount
   e. Estimates delivery time
   f. Creates Order + OrderItem records
   g. Clears the cart
   h. Sends notification to restaurant owner
7. Returns OrderResponse JSON to frontend
8. Frontend shows success toast and redirects to order tracking
```

---

## 5. Database Schema Design

### 5.1 Table Definitions

#### Table 1: `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique user identifier |
| `name` | VARCHAR(100) | NOT NULL | Full name |
| `email` | VARCHAR(150) | NOT NULL, UNIQUE, INDEXED | Login email |
| `password` | VARCHAR(255) | NOT NULL | Hashed password (PBKDF2-SHA256) |
| `role` | VARCHAR(20) | NOT NULL | One of: `admin`, `owner`, `customer`, `delivery`, `care` |
| `pin_code` | VARCHAR(10) | NOT NULL | User's service area |

---

#### Table 2: `restaurants`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique restaurant identifier |
| `name` | VARCHAR(200) | NOT NULL | Restaurant name |
| `pin_code` | VARCHAR(10) | NOT NULL | Service area PIN code |
| `status` | VARCHAR(20) | DEFAULT 'active' | active or inactive |
| `restaurant_fee` | FLOAT | DEFAULT 0.0 | Flat fee added to every order |
| `owner_id` | INTEGER | FK → users.id, NULLABLE | Linked restaurant owner |

---

#### Table 3: `dishes`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique dish identifier |
| `name` | VARCHAR(200) | NOT NULL | Dish name |
| `price` | FLOAT | NOT NULL | Dish price in ₹ |
| `image_path` | VARCHAR(500) | DEFAULT '' | URL to dish image |
| `availability` | BOOLEAN | DEFAULT TRUE | Whether dish can be ordered |
| `restaurant_id` | INTEGER | FK → restaurants.id, NOT NULL | Parent restaurant |

---

#### Table 4: `delivery_partners`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique partner identifier |
| `user_id` | INTEGER | FK → users.id, UNIQUE, NOT NULL | Linked user account |
| `availability` | BOOLEAN | DEFAULT TRUE | Whether partner is free for delivery |
| `pin_code` | VARCHAR(10) | NOT NULL | Service area PIN code |

---

#### Table 5: `orders`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique order identifier |
| `customer_id` | INTEGER | FK → users.id, NOT NULL | Customer who placed the order |
| `restaurant_id` | INTEGER | FK → restaurants.id, NOT NULL | Restaurant from which order is placed |
| `total_amount` | FLOAT | NOT NULL | Final amount after fee and discount |
| `discount_amount` | FLOAT | DEFAULT 0.0 | Discount applied |
| `restaurant_fee` | FLOAT | DEFAULT 0.0 | Restaurant fee charged |
| `payment_mode` | VARCHAR(30) | DEFAULT 'online' | online, cod, or upi |
| `order_status` | VARCHAR(30) | DEFAULT 'Placed' | Current status in lifecycle |
| `delivery_partner_id` | INTEGER | FK → delivery_partners.id, NULLABLE | Assigned delivery partner |
| `offer_id` | INTEGER | FK → offers.id, NULLABLE | Offer applied to this order |
| `estimated_delivery_time` | INTEGER | NULLABLE | Estimated time in minutes |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Order creation timestamp |

---

#### Table 6: `order_items`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique item identifier |
| `order_id` | INTEGER | FK → orders.id, NOT NULL | Parent order |
| `dish_id` | INTEGER | FK → dishes.id, NOT NULL | Ordered dish |
| `quantity` | INTEGER | NOT NULL | Number of servings |
| `price` | FLOAT | NOT NULL | Price at time of order (snapshot) |

---

#### Table 7: `offers`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique offer identifier |
| `description` | VARCHAR(300) | NOT NULL | Human-readable offer text |
| `discount_percentage` | FLOAT | NOT NULL | Discount % (1–100) |
| `minimum_order_value` | FLOAT | NOT NULL | Minimum subtotal required |
| `applicable_type` | VARCHAR(20) | NOT NULL | 'platform' or 'restaurant' |
| `restaurant_id` | INTEGER | FK → restaurants.id, NULLABLE | NULL for platform offers |
| `active` | BOOLEAN | DEFAULT TRUE | Whether offer is currently active |

---

#### Table 8: `complaints`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique complaint identifier |
| `order_id` | INTEGER | FK → orders.id, NOT NULL | Related order |
| `customer_id` | INTEGER | FK → users.id, NOT NULL | Customer who filed |
| `description` | TEXT | NOT NULL | Issue description |
| `status` | VARCHAR(30) | DEFAULT 'Open' | Open / In Progress / Resolved / Closed |
| `resolution_notes` | TEXT | NULLABLE | Notes from customer care |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Filing timestamp |

---

#### Table 9: `cart`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique cart item identifier |
| `customer_id` | INTEGER | FK → users.id, NOT NULL | Cart owner |
| `dish_id` | INTEGER | FK → dishes.id, NOT NULL | Selected dish |
| `restaurant_id` | INTEGER | FK → restaurants.id, NOT NULL | Restaurant (for single-restaurant constraint) |
| `quantity` | INTEGER | DEFAULT 1 | Number of servings |

---

#### Table 10: `notifications`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO-INCREMENT | Unique notification identifier |
| `user_id` | INTEGER | FK → users.id, NOT NULL | Notification recipient |
| `message` | VARCHAR(500) | NOT NULL | Notification text |
| `is_read` | BOOLEAN | DEFAULT FALSE | Read status |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

---

### 5.2 Summary of Keys

| Table | Primary Key | Foreign Keys |
|---|---|---|
| users | id | — |
| restaurants | id | owner_id → users.id |
| dishes | id | restaurant_id → restaurants.id |
| delivery_partners | id | user_id → users.id |
| orders | id | customer_id → users.id, restaurant_id → restaurants.id, delivery_partner_id → delivery_partners.id, offer_id → offers.id |
| order_items | id | order_id → orders.id, dish_id → dishes.id |
| offers | id | restaurant_id → restaurants.id |
| complaints | id | order_id → orders.id, customer_id → users.id |
| cart | id | customer_id → users.id, dish_id → dishes.id, restaurant_id → restaurants.id |
| notifications | id | user_id → users.id |

**Total:** 10 tables, 10 primary keys, 16 foreign key relationships.

---

## 6. Entity Relationships Explanation

### 6.1 Text-Based ER Diagram

```
┌──────────┐       1          N       ┌──────────────┐
│  USERS   │ ──────────────────────── │  ORDERS      │
│          │  (customer places)       │              │
└────┬─────┘                          └───────┬──────┘
     │                                        │
     │ 1                                      │ 1
     │         N                              │         N
     ├──────────── NOTIFICATIONS              ├──────────── ORDER_ITEMS
     │                                        │
     │ 1                                      │ 1
     │         N                              │         N
     ├──────────── COMPLAINTS                 ├──────────── COMPLAINTS
     │                                        │
     │ 1                                      │
     │         N                              │
     ├──────────── CART                       │
     │                                        │
     │ 1                                      │
     │         1                              │
     └──────────── DELIVERY_PARTNERS          │
                        │                     │
                        │ 1            N      │
                        └─────────────────────┘
                          (partner delivers)

┌──────────────┐     1          N     ┌──────────┐
│ RESTAURANTS  │ ──────────────────── │  DISHES  │
│              │                      │          │
└──────┬───────┘                      └──────────┘
       │
       │ 1           N
       ├──────────────── ORDERS
       │
       │ 1           N
       ├──────────────── OFFERS
       │
       │ 1           N
       └──────────────── CART

┌──────────┐     1          N     ┌──────────────┐
│  OFFERS  │ ──────────────────── │   ORDERS     │
│          │  (offer applied to)  │              │
└──────────┘                      └──────────────┘
```

### 6.2 Relationship Descriptions

| Relationship | Type | Description |
|---|---|---|
| **User → Orders** | One-to-Many | One customer can place many orders. Each order belongs to exactly one customer. |
| **User → Notifications** | One-to-Many | Each user can receive many notifications. |
| **User → Complaints** | One-to-Many | A customer can file many complaints. |
| **User → Cart** | One-to-Many | A customer can have multiple items in their cart. |
| **User → Delivery Partner** | One-to-One | Each delivery user has exactly one delivery partner profile. |
| **Restaurant → Dishes** | One-to-Many | A restaurant has many dishes. Dishes are cascade-deleted when a restaurant is removed. |
| **Restaurant → Orders** | One-to-Many | Many orders can be placed from one restaurant. |
| **Restaurant → Offers** | One-to-Many | A restaurant can have multiple restaurant-specific offers. Platform offers have a NULL restaurant_id. |
| **Restaurant → Cart** | One-to-Many | Cart items reference their source restaurant (used for single-restaurant constraint). |
| **Restaurant → Owner (User)** | Many-to-One | Each restaurant is linked to one owner user. An owner may manage multiple restaurants. |
| **Order → Order Items** | One-to-Many | Each order contains multiple items. Items are cascade-deleted with the order. |
| **Order → Delivery Partner** | Many-to-One | Many orders can be assigned to one delivery partner (over time), but each order has at most one partner. |
| **Order → Offer** | Many-to-One | Many orders can use the same offer. Each order has at most one offer applied. |
| **Order → Complaints** | One-to-Many | One order can have multiple complaints filed against it. |
| **Dish → Order Items** | One-to-Many | A dish can appear in many order items across different orders. |
| **Dish → Cart** | One-to-Many | A dish can be in multiple carts of different customers. |

---

## 7. API Endpoint Planning

All APIs use JSON request/response format with JWT Bearer token authentication (except public auth endpoints).

### 7.1 Authentication APIs (Public)

| Method | Endpoint | Purpose | Request Body |
|---|---|---|---|
| POST | `/api/auth/register` | Create new user account | name, email, password, role, pin_code |
| POST | `/api/auth/login` | Login and receive JWT token | email, password |
| GET | `/api/auth/me` | Get current user profile | — (token only) |

---

### 7.2 Admin APIs (Role: `admin`)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/admin/restaurants` | List all restaurants on the platform |
| POST | `/api/admin/restaurants` | Add a new restaurant |
| PUT | `/api/admin/restaurants/{id}` | Update restaurant details (name, PIN, status, fee, owner) |
| GET | `/api/admin/offers` | List all platform-level offers |
| POST | `/api/admin/offers` | Create a new platform-level offer |
| DELETE | `/api/admin/offers/{id}` | Delete a platform offer |
| GET | `/api/admin/stats` | Get platform-wide statistics |

**Stats Response Includes:** total_orders, total_revenue, total_restaurants, total_customers, total_delivery_partners, orders_by_status (grouped count).

---

### 7.3 Restaurant Owner APIs (Role: `owner`)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/owner/restaurant` | Get own restaurant info |
| GET | `/api/owner/dishes` | List all dishes in own restaurant |
| POST | `/api/owner/dishes` | Add a new dish |
| PUT | `/api/owner/dishes/{id}` | Update dish (name, price, image, availability) |
| DELETE | `/api/owner/dishes/{id}` | Remove a dish |
| GET | `/api/owner/orders` | List all orders for own restaurant |
| PUT | `/api/owner/orders/{id}/status` | Update order status (strict transitions) |
| GET | `/api/owner/offers` | List own restaurant-level offers |
| POST | `/api/owner/offers` | Create restaurant-level offer |

---

### 7.4 Customer APIs (Role: `customer`)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/customer/restaurants` | Browse restaurants in own PIN code |
| GET | `/api/customer/restaurants/{id}/menu` | View menu for a restaurant |
| GET | `/api/customer/cart` | View current cart |
| POST | `/api/customer/cart` | Add item to cart |
| DELETE | `/api/customer/cart/{id}` | Remove specific item from cart |
| DELETE | `/api/customer/cart` | Clear entire cart |
| GET | `/api/customer/offers?restaurant_id=X` | Get eligible offers for a restaurant |
| POST | `/api/customer/checkout` | Place order from cart |
| GET | `/api/customer/orders` | View order history |
| GET | `/api/customer/orders/{id}` | View specific order details |
| POST | `/api/customer/orders/{id}/reorder` | Reorder from past order |
| POST | `/api/customer/complaints` | Raise a complaint |
| GET | `/api/customer/complaints` | View own complaints |

---

### 7.5 Delivery Partner APIs (Role: `delivery`)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/delivery/status` | Get own availability status |
| PUT | `/api/delivery/availability` | Toggle availability (online/offline) |
| GET | `/api/delivery/orders` | View assigned deliveries |
| PUT | `/api/delivery/orders/{id}/deliver` | Mark order as Delivered |

---

### 7.6 Customer Care APIs (Role: `care`)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/care/complaints` | View all complaints across platform |
| PUT | `/api/care/complaints/{id}` | Update complaint status and resolution notes |
| GET | `/api/care/orders` | View all orders (for referencing during complaints) |
| PUT | `/api/care/orders/{id}/cancel` | Cancel an order |

---

### 7.7 Shared APIs (Any Authenticated User)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/notifications` | Get user's recent notifications (last 20) |
| PUT | `/api/notifications/read` | Mark all notifications as read |

---

### 7.8 API Count Summary

| Role | GET | POST | PUT | DELETE | Total |
|---|---|---|---|---|---|
| Auth (public) | 1 | 2 | — | — | 3 |
| Admin | 3 | 2 | 1 | 1 | 7 |
| Owner | 4 | 2 | 2 | 1 | 9 |
| Customer | 6 | 3 | — | 2 | 11 |
| Delivery | 2 | — | 2 | — | 4 |
| Care | 2 | — | 2 | — | 4 |
| Shared | 1 | — | 1 | — | 2 |
| **Total** | **19** | **9** | **8** | **4** | **40** |

---

## 8. UI Screen Planning

### 8.1 Screen Inventory

| Screen | File | Target Role | Key Components |
|---|---|---|---|
| **Login / Register** | index.html | All | Login form, Registration form with role selector, toggle between forms |
| **Customer Dashboard** | customer.html | Customer | 5 tabs (Restaurants, Menu, Cart, Orders, Complaints) |
| **Admin Dashboard** | admin.html | Admin | 3 tabs (Statistics, Restaurants, Offers) |
| **Owner Dashboard** | owner.html | Owner | 3 tabs (Orders, Dishes, Offers) |
| **Delivery Dashboard** | delivery.html | Delivery | 2 tabs (Status, Deliveries) |
| **Care Dashboard** | care.html | Care | 2 tabs (Complaints, Orders) |

**Total:** 6 HTML pages, each with tab-based navigation for sub-sections.

---

### 8.2 Detailed Screen Layouts

#### Screen 1: Login / Register (index.html)

```
┌──────────────────────────────────────┐
│  🍽️ PinDrop Eats             Navbar │
├──────────────────────────────────────┤
│                                      │
│   ┌──────────────────────────────┐   │
│   │        Welcome Back          │   │
│   │                              │   │
│   │   Email:    [____________]   │   │
│   │   Password: [____________]   │   │
│   │                              │   │
│   │   [      LOGIN BUTTON      ] │   │
│   │                              │   │
│   │   Don't have an account?     │   │
│   │   Register here              │   │
│   └──────────────────────────────┘   │
│                                      │
└──────────────────────────────────────┘
```

- After login, user is automatically redirected to their role-specific dashboard.
- Registration form adds: Name, Role dropdown, PIN code fields.

---

#### Screen 2: Customer Dashboard (customer.html)

**Tab: Restaurants**
```
┌──────────────────────────────────────────────────┐
│  Restaurants near you (PIN: 110001)              │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Banner  │  │  Banner  │  │  Banner  │       │
│  │ Spice    │  │ Tandoor  │  │          │       │
│  │ Garden   │  │ House    │  │ ...      │       │
│  │ PIN: ... │  │ Fee: ₹30 │  │          │       │
│  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────┘
```

**Tab: Menu** — Grid of dish cards with image, name, price, availability, and "Add to Cart" button.

**Tab: Cart**
```
┌──────────────────────────────────────────────────┐
│  Your Cart — Spice Garden                        │
│                                                  │
│  [Img] Butter Chicken  ₹280 × 1    ₹280   [✕]  │
│  [Img] Dal Makhani     ₹180 × 2    ₹360   [✕]  │
│                                                  │
│  ┌─ Apply Offer ────────────────────────┐        │
│  │ [Dropdown: Select offer           ▼] │        │
│  │ ✅ 20% off applied! Saving ₹128.00   │        │
│  └──────────────────────────────────────┘        │
│                                                  │
│  Subtotal:        ₹640.00                        │
│  Restaurant Fee:   ₹25.00                        │
│  Discount:        -₹128.00                       │
│  ─────────────────────────                       │
│  Total:           ₹537.00                        │
│                                                  │
│  Payment: [Online ▼]                             │
│                                                  │
│  [Clear Cart]              [Place Order]         │
└──────────────────────────────────────────────────┘
```

**Tab: Orders** — Order cards with status badge, visual timeline, item list, total, and Reorder + Raise Complaint buttons.

**Tab: Complaints** — Complaint submission form + table of filed complaints with status tracking.

---

#### Screen 3: Admin Dashboard (admin.html)

**Tab: Statistics**
```
┌──────────────────────────────────────────────────┐
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │  12  │  │₹8500 │  │   4  │  │   5  │         │
│  │Orders│  │Rev.  │  │Rest. │  │Cust. │         │
│  └──────┘  └──────┘  └──────┘  └──────┘         │
│                                                  │
│  Orders by Status:                               │
│  Placed: 3 | Accepted: 2 | Delivered: 7         │
└──────────────────────────────────────────────────┘
```

**Tab: Restaurants** — Table of all restaurants with Add/Edit actions.

**Tab: Offers** — Table of platform offers with Add/Delete actions.

---

#### Screen 4: Owner Dashboard (owner.html)

**Tab: Orders** — List of incoming orders with Accept/Reject/Preparing/Send for Delivery action buttons based on current status.

**Tab: Dishes** — Grid of dish cards with availability toggle and delete. Add dish form at top.

**Tab: Offers** — Table of restaurant-specific offers with creation form.

---

#### Screen 5: Delivery Dashboard (delivery.html)

**Tab: Status** — Large availability indicator (🟢/🔴) with toggle button.

**Tab: Deliveries** — List of assigned orders with "Mark as Delivered" button for active deliveries.

---

#### Screen 6: Care Dashboard (care.html)

**Tab: Complaints** — Each complaint shown as a card with: order reference, customer name, description, status dropdown, resolution notes input, update button, and cancel order button.

**Tab: Orders** — Table of all orders with status and cancel action.

---

### 8.3 Shared UI Components

| Component | Description |
|---|---|
| **Navbar** | Brand logo, notification bell with unread badge, user info (name, role, PIN), logout button. Present on all dashboards. |
| **Toast Notifications** | Slide-in from top-right. Green for success, red for error. Auto-dismiss after 4 seconds. |
| **Status Badges** | Colour-coded pills: yellow (Placed), blue (Accepted), amber (Preparing), green (Delivered), red (Cancelled/Rejected). |
| **Order Timeline** | Horizontal 5-step progress indicator (dots + labels). Completed steps are green, current step is orange. |
| **Notification Dropdown** | Slides down from bell icon. Shows last 20 notifications. Unread items highlighted. |

---

## 9. Business Rules Enforcement Strategy

This section maps each business rule to its specific enforcement mechanism in the system design.

### Rule 1: Customers only see restaurants in their PIN code area

| Layer | Enforcement |
|---|---|
| **API** | `GET /api/customer/restaurants` filters by `WHERE restaurant.pin_code = user.pin_code AND status = 'active'`. |
| **API** | `GET /api/customer/restaurants/{id}/menu` verifies `restaurant.pin_code == user.pin_code` before returning dishes. |
| **API** | `POST /api/customer/cart` verifies the dish's restaurant is in the customer's PIN code area. |
| **Frontend** | Only displays restaurants returned by the filtered API. Customer cannot manually enter a restaurant URL for a different area. |

---

### Rule 2: Cannot add unavailable dishes to cart

| Layer | Enforcement |
|---|---|
| **API (Add to Cart)** | Checks `dish.availability == True` before adding. Returns 400 error if unavailable. |
| **API (Checkout)** | Re-validates every cart item's availability at checkout time. Rejects stale items. |
| **Frontend** | Shows "Unavailable" label and disables "Add to Cart" button for unavailable dishes. |

---

### Rule 3: Offers apply only if minimum order value is met

| Layer | Enforcement |
|---|---|
| **API (Checkout)** | Compares cart subtotal against `offer.minimum_order_value`. Returns 400 if subtotal < minimum. |
| **API (Checkout)** | Validates offer is `active == True` and (if restaurant-level) matches the cart's restaurant. |
| **Frontend** | Displays warning message if subtotal is below the selected offer's minimum, showing the shortfall amount. |

---

### Rule 4: Order total = (sum of items) + restaurant fee − discount

| Layer | Enforcement |
|---|---|
| **API (Checkout)** | Calculates: `subtotal = Σ(dish.price × quantity)`, then `total = subtotal + restaurant.restaurant_fee − (subtotal × discount_percentage / 100)`. Stores `total_amount`, `discount_amount`, and `restaurant_fee` separately in the order record. |
| **Frontend** | Displays itemised breakdown in cart before checkout: subtotal, fee, discount, total. |

---

### Rule 5: Delivery partner assigned only if available and in same PIN code

| Layer | Enforcement |
|---|---|
| **API (Status Update)** | When owner transitions order to "Out for Delivery", system queries: `SELECT FROM delivery_partners WHERE availability = TRUE AND pin_code = restaurant.pin_code`. |
| **API** | If no partner found → transition is **blocked** with a 400 error. |
| **API** | If partner found → sets `order.delivery_partner_id`, sets `partner.availability = FALSE`. |
| **API (Mark Delivered)** | On delivery completion, sets `partner.availability = TRUE` (frees for next assignment). |

---

### Rule 6: Order status must follow Placed → Accepted → Preparing → Out for Delivery → Delivered

| Layer | Enforcement |
|---|---|
| **API (Owner)** | Maintains a transition map: `{"Placed": ["Accepted", "Rejected"], "Accepted": ["Preparing"], "Preparing": ["Out for Delivery"]}`. Any other transition returns a 400 error with the allowed transitions listed. |
| **API (Delivery)** | Only allows `"Out for Delivery" → "Delivered"`. |
| **API (Care)** | Only allows cancellation from non-terminal states (not Delivered/Cancelled/Rejected). |

---

### Rule 7: No skipping of order states allowed

| Layer | Enforcement |
|---|---|
| **API** | The transition map (Rule 6) is the **sole** mechanism for status changes. There is no "set status" endpoint that accepts arbitrary values. |
| **API** | Each endpoint checks `current_status` and validates `new_status` against the allowed list. |
| **Database** | Status is stored as a string (not an integer), making the transition logic explicit and auditable in code. |

---

### Additional Business Rules Enforced

| Rule | Enforcement |
|---|---|
| **Single-restaurant cart** | Adding a dish from restaurant B when cart has items from restaurant A returns 400: "Clear your cart first." |
| **Duplicate dish in cart** | Adding a dish already in cart increments quantity instead of creating a new row. |
| **Password security** | Passwords are hashed using PBKDF2-SHA256. Minimum 6 characters enforced by Pydantic validator. |
| **Email uniqueness** | Database UNIQUE constraint on `users.email`. Registration returns 400 if email exists. |
| **Role-based access** | Each API router uses a `require_role()` dependency that checks `user.role` against allowed roles. Returns 403 on mismatch. |
| **Offer type restriction** | Admin can only create `applicable_type = "platform"` offers. Owner can only create `applicable_type = "restaurant"` offers. |

---

## 10. Assumptions Made

### 10.1 Functional Assumptions

| # | Assumption | Rationale |
|---|---|---|
| 1 | Each user has exactly one role. | Simplifies auth model. An admin does not also act as a customer within the same account. |
| 2 | PIN code is a string of up to 10 characters. | Covers Indian 6-digit pins and leaves room for international formats. |
| 3 | A single restaurant owner can manage multiple restaurants (via admin assigning `owner_id`). | Reflects real-world franchise scenarios. |
| 4 | Cart is persistent (stored in DB), not session-based. | Allows customers to resume shopping across browser sessions. |
| 5 | Payment is simulated (no real payment gateway). | Focus is on order lifecycle, not payment processing. |
| 6 | Delivery partner assignment is "first available" (not nearest or load-balanced). | Simplifies assignment logic for the current scope. |
| 7 | Dish images are stored as URLs (not uploaded files). | Reduces server storage complexity. Sample data uses Unsplash URLs. |
| 8 | One offer per order. | Simplifies discount calculation. Stacking offers is out of scope. |

### 10.2 Technical Assumptions

| # | Assumption | Rationale |
|---|---|---|
| 1 | SQLite is sufficient for development and demonstration. | No concurrent write-heavy production load expected. Migration to PostgreSQL is straightforward via SQLAlchemy. |
| 2 | JWT tokens have a 24-hour expiry. | Balances security with usability for demonstration purposes. |
| 3 | Frontend is served as static files (no build step). | Keeps deployment simple. No Node.js or npm required. |
| 4 | Notifications are polling-based (frontend polls every 15 seconds). | WebSocket integration is out of scope for Sprint 1. |
| 5 | All users on the same machine can access via localhost. | This is a local development/demo project, not a cloud deployment. |

---

## 11. Task Allocation for Team of 3

### 11.1 Team Structure

| Member | Role | Primary Focus |
|---|---|---|
| **Member A** | Backend Lead | Database models, Auth system, Core API logic |
| **Member B** | Backend + Business Logic | Role-based routers, Order lifecycle, Business rules |
| **Member C** | Frontend Lead | UI pages, API integration, CSS styling |

---

### 11.2 Sprint 1 Task Breakdown

#### Week 1: Foundation (Days 1–3)

| Task | Assigned To | Estimated Hours | Deliverable |
|---|---|---|---|
| Database schema design and model creation | Member A | 6h | models.py with all 10 tables |
| Auth system (JWT + password hashing + role checking) | Member A | 4h | auth.py with login/register |
| Pydantic schemas for request/response validation | Member B | 4h | schemas.py with all DTOs |
| System architecture documentation | Member B | 3h | Architecture section of design doc |
| Frontend boilerplate (HTML structure, CSS design system) | Member C | 5h | style.css + index.html |
| Shared JS utility module (API client, auth, toasts) | Member C | 4h | app.js |

#### Week 1: Core Features (Days 4–7)

| Task | Assigned To | Estimated Hours | Deliverable |
|---|---|---|---|
| Admin router (restaurants, offers, stats) | Member A | 5h | admin.py router |
| Restaurant owner router (dishes, orders, status transitions) | Member B | 6h | restaurant_owner.py router |
| Customer router (browse, cart, checkout, orders) | Member B | 8h | customer.py router |
| Delivery partner router (availability, deliver) | Member A | 3h | delivery.py router |
| Customer care router (complaints, cancel) | Member A | 3h | customer_care.py router |
| Customer UI (restaurants, menu, cart, checkout, orders) | Member C | 10h | customer.html |
| Admin + Owner UI | Member C | 6h | admin.html + owner.html |

#### Week 2: Polish & Integration (Days 8–10)

| Task | Assigned To | Estimated Hours | Deliverable |
|---|---|---|---|
| Delivery + Care UI | Member C | 4h | delivery.html + care.html |
| Seed data script | Member A | 2h | seed.py |
| Notification system (server + frontend bell) | Member B | 4h | Notification model + API + UI widget |
| Innovation features (delivery estimate, reorder) | Member B | 3h | Estimation algorithm + reorder endpoint |
| End-to-end testing of full demo flow | All | 4h | Verified demo flow |
| Documentation (README, API list, design doc) | All | 3h | README.md + design doc |

---

### 11.3 Task Dependencies

```
models.py + auth.py (Member A)
        ↓
schemas.py (Member B) ←── Can start simultaneously
        ↓
   Admin Router (A) ──┐
   Owner Router (B) ──┤── All routers depend on models + schemas
   Customer Router (B)┤
   Delivery Router (A)┤
   Care Router (A) ───┘
        ↓
   Frontend pages (C) ←── Frontend development can begin with mock data
        ↓                  in parallel, then connects to real APIs
   Integration Testing (All)
```

---

## 12. How This Design Satisfies Evaluation Criteria

### 12.1 Problem Understanding ✅

| Evidence | Details |
|---|---|
| Clear problem breakdown | Section 1 identifies 5 distinct problem areas and 5 stakeholders |
| Role definitions | Section 2 specifies each role's responsibilities with concrete actions |
| Business rule formalization | Section 9 maps all 7+ rules to enforcement mechanisms across API, DB, and frontend layers |
| Lifecycle documentation | Section 3 provides a complete state diagram with transition rules and side effects |

---

### 12.2 Data & System Design ✅

| Evidence | Details |
|---|---|
| 10 well-normalized tables | Section 5 provides column-level detail for every table |
| 16 foreign key relationships | Section 5.2 summarises all FK relationships |
| Entity relationship explanation | Section 6 provides both a diagram and a descriptive table of all relationships |
| Architecture diagram | Section 4 shows the full system architecture with all layers |
| Technology justification | Section 4.2 explains each tech choice with rationale |

---

### 12.3 Backend Engineering Readiness ✅

| Evidence | Details |
|---|---|
| 40 API endpoints planned | Section 7 lists every endpoint with method, path, and purpose |
| Role-based endpoint grouping | Each role has its own API prefix and router |
| Request flow walkthrough | Section 4.3 traces a complete checkout from click to response |
| Status transition machine | Sections 3.2 and 9 (Rule 6) define explicit transition maps |
| Validation strategy | Pydantic schemas handle input validation; API layer handles business rules |
| Error handling approach | Each rule violation returns specific HTTP status codes (400, 403, 404) with descriptive messages |

---

### 12.4 UI Planning ✅

| Evidence | Details |
|---|---|
| 6 screens identified | Section 8.1 maps each HTML page to its role and tab structure |
| Wireframe-level layouts | Section 8.2 provides text-based wireframes for key screens (Cart, Stats, etc.) |
| Shared component library | Section 8.3 documents reusable UI elements (navbar, toasts, badges, timeline) |
| User flow mapped | Cart → Apply Offer → Checkout flow is fully designed |

---

### 12.5 Innovation Readiness ✅

| Feature | Design Approach |
|---|---|
| **Delivery Time Estimation** | Algorithm: `base 25 min + 2 min per item ± random variance`. Floored at 15 minutes. Stored in `orders.estimated_delivery_time`. Displayed on order cards and tracking page. |
| **Reorder from Past Orders** | `POST /api/customer/orders/{id}/reorder` copies past order items to cart. Skips unavailable dishes. Reports added vs. skipped count. Clears existing cart first. |
| **Real-Time Notifications** | Server-side `notifications` table. Triggers on: order status change, delivery assignment, delivery completion, complaint update, order cancellation. Frontend bell icon with unread count, auto-refresh every 15 seconds. |

All three innovation features are designed into the schema (notification table, estimated_delivery_time column) and API (reorder endpoint, notification endpoints) from the start, ensuring they are not bolted on later.

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| **PIN Code** | Postal Index Number. Used to define service areas for restaurants, customers, and delivery partners. |
| **JWT** | JSON Web Token. A compact, URL-safe token used for stateless authentication. |
| **ORM** | Object-Relational Mapping. SQLAlchemy translates Python objects to SQL queries. |
| **DTO** | Data Transfer Object. Pydantic schemas that define the shape of API requests and responses. |
| **CORS** | Cross-Origin Resource Sharing. Middleware that allows the frontend (on port 5500) to call the backend (on port 8000). |
| **State Machine** | A model where order status can only transition through predefined valid paths. |
| **Cascade Delete** | When a parent record (e.g., restaurant) is deleted, all child records (e.g., dishes) are automatically deleted. |

---

## Appendix B: Sample Seed Data

The system ships with pre-loaded test data for immediate demonstration:

| Entity | Count | Details |
|---|---|---|
| Users | 8 | 1 admin, 2 owners, 2 customers, 2 delivery partners, 1 care executive |
| Restaurants | 4 | 2 in PIN 110001, 2 in PIN 110002 |
| Dishes | 19 | Indian, Italian, and Chinese cuisine with Unsplash images |
| Delivery Partners | 2 | 1 per PIN code |
| Offers | 4 | 2 platform-wide, 2 restaurant-specific |

All test accounts use the password: `password123`

---

*Document prepared for Sprint 1 submission — PinDrop Eats Team*
*Date: February 24, 2026*
