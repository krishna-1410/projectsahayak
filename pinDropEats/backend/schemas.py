from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ── Auth ─────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    pin_code: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed = ["admin", "owner", "customer", "delivery", "care"]
        if v not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    pin_code: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Restaurant ───────────────────────────────────────
class RestaurantCreate(BaseModel):
    name: str
    pin_code: str
    restaurant_fee: float = 0.0
    owner_id: Optional[int] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    pin_code: Optional[str] = None
    status: Optional[str] = None
    restaurant_fee: Optional[float] = None
    owner_id: Optional[int] = None


class RestaurantResponse(BaseModel):
    id: int
    name: str
    pin_code: str
    status: str
    restaurant_fee: float
    owner_id: Optional[int]

    class Config:
        from_attributes = True


# ── Dish ─────────────────────────────────────────────
class DishCreate(BaseModel):
    name: str
    price: float
    image_path: str = ""
    availability: bool = True
    restaurant_id: int


class DishUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    image_path: Optional[str] = None
    availability: Optional[bool] = None


class DishResponse(BaseModel):
    id: int
    name: str
    price: float
    image_path: str
    availability: bool
    restaurant_id: int

    class Config:
        from_attributes = True


# ── Order ────────────────────────────────────────────
class OrderItemResponse(BaseModel):
    id: int
    dish_id: int
    quantity: int
    price: float
    dish_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    total_amount: float
    discount_amount: float
    restaurant_fee: float
    payment_mode: str
    order_status: str
    delivery_partner_id: Optional[int]
    estimated_delivery_time: Optional[int]
    created_at: datetime
    items: List[OrderItemResponse] = []
    restaurant_name: Optional[str] = None
    customer_name: Optional[str] = None
    delivery_partner_name: Optional[str] = None

    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    payment_mode: str = "online"
    offer_id: Optional[int] = None


class OrderStatusUpdate(BaseModel):
    status: str


# ── Offer ────────────────────────────────────────────
class OfferCreate(BaseModel):
    description: str
    discount_percentage: float
    minimum_order_value: float
    applicable_type: str  # platform, restaurant
    restaurant_id: Optional[int] = None

    @field_validator("applicable_type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["platform", "restaurant"]:
            raise ValueError("applicable_type must be 'platform' or 'restaurant'")
        return v

    @field_validator("discount_percentage")
    @classmethod
    def validate_discount(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        return v


class OfferResponse(BaseModel):
    id: int
    description: str
    discount_percentage: float
    minimum_order_value: float
    applicable_type: str
    restaurant_id: Optional[int]
    active: bool

    class Config:
        from_attributes = True


# ── Cart ─────────────────────────────────────────────
class CartAdd(BaseModel):
    dish_id: int
    quantity: int = 1


class CartUpdateQuantity(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    dish_id: int
    restaurant_id: int
    quantity: int
    dish_name: Optional[str] = None
    dish_price: Optional[float] = None
    dish_image: Optional[str] = None
    restaurant_name: Optional[str] = None

    class Config:
        from_attributes = True


# ── Complaint ────────────────────────────────────────
class ComplaintCreate(BaseModel):
    order_id: int
    description: str


class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


class ComplaintResponse(BaseModel):
    id: int
    order_id: int
    customer_id: int
    description: str
    status: str
    resolution_notes: Optional[str]
    created_at: datetime
    customer_name: Optional[str] = None

    class Config:
        from_attributes = True


# ── Notification ─────────────────────────────────────
class NotificationResponse(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Delivery Partner ─────────────────────────────────
class DeliveryPartnerResponse(BaseModel):
    id: int
    user_id: int
    availability: bool
    pin_code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


# ── Stats ────────────────────────────────────────────
class PlatformStats(BaseModel):
    total_orders: int
    total_revenue: float
    total_restaurants: int
    total_customers: int
    total_delivery_partners: int
    orders_by_status: dict
