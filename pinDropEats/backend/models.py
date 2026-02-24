from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin, owner, customer, delivery, care
    pin_code = Column(String(10), nullable=False)

    orders = relationship("Order", back_populates="customer", foreign_keys="Order.customer_id")
    notifications = relationship("Notification", back_populates="user")
    complaints = relationship("Complaint", back_populates="customer")
    cart_items = relationship("Cart", back_populates="customer")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    pin_code = Column(String(10), nullable=False)
    status = Column(String(20), default="active")
    restaurant_fee = Column(Float, default=0.0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    dishes = relationship("Dish", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")
    offers = relationship("Offer", back_populates="restaurant")
    owner = relationship("User", foreign_keys=[owner_id])


class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    image_path = Column(String(500), default="")
    availability = Column(Boolean, default=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    restaurant = relationship("Restaurant", back_populates="dishes")


class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    availability = Column(Boolean, default=True)
    pin_code = Column(String(10), nullable=False)

    user = relationship("User", foreign_keys=[user_id])


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    restaurant_fee = Column(Float, default=0.0)
    payment_mode = Column(String(30), default="online")
    order_status = Column(String(30), default="Placed")
    delivery_partner_id = Column(Integer, ForeignKey("delivery_partners.id"), nullable=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True)
    estimated_delivery_time = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery_partner = relationship("DeliveryPartner", foreign_keys=[delivery_partner_id])
    complaints = relationship("Complaint", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    dish = relationship("Dish")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(300), nullable=False)
    discount_percentage = Column(Float, nullable=False)
    minimum_order_value = Column(Float, nullable=False)
    applicable_type = Column(String(20), nullable=False)  # platform, restaurant
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    active = Column(Boolean, default=True)

    restaurant = relationship("Restaurant", back_populates="offers")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="Open")
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="complaints")
    customer = relationship("User", back_populates="complaints")


class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    quantity = Column(Integer, default=1)

    customer = relationship("User", back_populates="cart_items")
    dish = relationship("Dish")
    restaurant = relationship("Restaurant")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
