import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import require_role, create_notification, get_current_user
import models
import schemas

router = APIRouter(prefix="/api/customer", tags=["Customer"])


# ── Browse Restaurants ───────────────────────────────
@router.get("/restaurants", response_model=list[schemas.RestaurantResponse])
def browse_restaurants(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    """Customers only see restaurants in their pin code area."""
    return (
        db.query(models.Restaurant)
        .filter(
            models.Restaurant.pin_code == user.pin_code,
            models.Restaurant.status == "active",
        )
        .all()
    )


@router.get("/restaurants/{restaurant_id}/menu", response_model=list[schemas.DishResponse])
def view_menu(
    restaurant_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    rest = db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()
    if not rest:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if rest.pin_code != user.pin_code:
        raise HTTPException(status_code=403, detail="Restaurant not in your area")
    return db.query(models.Dish).filter(models.Dish.restaurant_id == restaurant_id).all()


# ── Cart ─────────────────────────────────────────────
@router.get("/cart", response_model=list[schemas.CartItemResponse])
def get_cart(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    items = db.query(models.Cart).filter(models.Cart.customer_id == user.id).all()
    result = []
    for c in items:
        result.append(schemas.CartItemResponse(
            id=c.id,
            dish_id=c.dish_id,
            restaurant_id=c.restaurant_id,
            quantity=c.quantity,
            dish_name=c.dish.name if c.dish else None,
            dish_price=c.dish.price if c.dish else None,
            dish_image=c.dish.image_path if c.dish else None,
            restaurant_name=c.restaurant.name if c.restaurant else None,
        ))
    return result


@router.post("/cart", response_model=schemas.CartItemResponse)
def add_to_cart(
    data: schemas.CartAdd,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    dish = db.query(models.Dish).filter(models.Dish.id == data.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    if not dish.availability:
        raise HTTPException(status_code=400, detail="This dish is currently unavailable")

    rest = db.query(models.Restaurant).filter(models.Restaurant.id == dish.restaurant_id).first()
    if rest.pin_code != user.pin_code:
        raise HTTPException(status_code=403, detail="Restaurant not in your area")

    # Check if dish from a different restaurant already in cart
    existing_cart = db.query(models.Cart).filter(models.Cart.customer_id == user.id).first()
    if existing_cart and existing_cart.restaurant_id != dish.restaurant_id:
        raise HTTPException(
            status_code=400,
            detail="You can only order from one restaurant at a time. Clear your cart first.",
        )

    # Check if dish already in cart — update quantity
    existing_item = (
        db.query(models.Cart)
        .filter(models.Cart.customer_id == user.id, models.Cart.dish_id == data.dish_id)
        .first()
    )
    if existing_item:
        existing_item.quantity += data.quantity
        db.commit()
        db.refresh(existing_item)
        return schemas.CartItemResponse(
            id=existing_item.id,
            dish_id=existing_item.dish_id,
            restaurant_id=existing_item.restaurant_id,
            quantity=existing_item.quantity,
            dish_name=dish.name,
            dish_price=dish.price,
            dish_image=dish.image_path,
            restaurant_name=rest.name,
        )

    cart_item = models.Cart(
        customer_id=user.id,
        dish_id=data.dish_id,
        restaurant_id=dish.restaurant_id,
        quantity=data.quantity,
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return schemas.CartItemResponse(
        id=cart_item.id,
        dish_id=cart_item.dish_id,
        restaurant_id=cart_item.restaurant_id,
        quantity=cart_item.quantity,
        dish_name=dish.name,
        dish_price=dish.price,
        dish_image=dish.image_path,
        restaurant_name=rest.name,
    )


@router.delete("/cart/{item_id}")
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    item = (
        db.query(models.Cart)
        .filter(models.Cart.id == item_id, models.Cart.customer_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item removed from cart"}


@router.delete("/cart")
def clear_cart(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    db.query(models.Cart).filter(models.Cart.customer_id == user.id).delete()
    db.commit()
    return {"message": "Cart cleared"}


# ── Offers ───────────────────────────────────────────
@router.get("/offers", response_model=list[schemas.OfferResponse])
def get_eligible_offers(
    restaurant_id: int = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    """Get platform offers + restaurant offers for a given restaurant."""
    query = db.query(models.Offer).filter(models.Offer.active == True)
    if restaurant_id:
        offers = query.filter(
            (models.Offer.applicable_type == "platform")
            | (
                (models.Offer.applicable_type == "restaurant")
                & (models.Offer.restaurant_id == restaurant_id)
            )
        ).all()
    else:
        offers = query.filter(models.Offer.applicable_type == "platform").all()
    return offers


# ── Checkout ─────────────────────────────────────────
@router.post("/checkout", response_model=schemas.OrderResponse)
def checkout(
    data: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    cart_items = db.query(models.Cart).filter(models.Cart.customer_id == user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # All items must be from the same restaurant
    restaurant_id = cart_items[0].restaurant_id
    rest = db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()

    # Re-validate availability
    subtotal = 0.0
    order_items_data = []
    for ci in cart_items:
        dish = db.query(models.Dish).filter(models.Dish.id == ci.dish_id).first()
        if not dish or not dish.availability:
            raise HTTPException(
                status_code=400,
                detail=f"Dish '{dish.name if dish else ci.dish_id}' is no longer available",
            )
        item_total = dish.price * ci.quantity
        subtotal += item_total
        order_items_data.append({
            "dish_id": dish.id,
            "quantity": ci.quantity,
            "price": dish.price,
        })

    # Apply offer
    discount = 0.0
    if data.offer_id:
        offer = db.query(models.Offer).filter(models.Offer.id == data.offer_id, models.Offer.active == True).first()
        if not offer:
            raise HTTPException(status_code=400, detail="Invalid or inactive offer")
        if subtotal < offer.minimum_order_value:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum order value of ₹{offer.minimum_order_value} not met for this offer",
            )
        if offer.applicable_type == "restaurant" and offer.restaurant_id != restaurant_id:
            raise HTTPException(status_code=400, detail="This offer is not valid for this restaurant")
        discount = subtotal * (offer.discount_percentage / 100)

    restaurant_fee = rest.restaurant_fee
    total = subtotal + restaurant_fee - discount

    # Estimate delivery time: base 25 min + 2 min per item, ±5 min randomness
    total_items = sum(ci.quantity for ci in cart_items)
    estimated_time = 25 + (total_items * 2) + random.randint(-5, 5)
    estimated_time = max(estimated_time, 15)

    order = models.Order(
        customer_id=user.id,
        restaurant_id=restaurant_id,
        total_amount=round(total, 2),
        discount_amount=round(discount, 2),
        restaurant_fee=restaurant_fee,
        payment_mode=data.payment_mode,
        order_status="Placed",
        offer_id=data.offer_id,
        estimated_delivery_time=estimated_time,
    )
    db.add(order)
    db.flush()

    for oi in order_items_data:
        db.add(models.OrderItem(order_id=order.id, **oi))

    # Clear cart
    db.query(models.Cart).filter(models.Cart.customer_id == user.id).delete()
    db.commit()
    db.refresh(order)

    # Notify restaurant owner
    if rest.owner_id:
        create_notification(db, rest.owner_id, f"New order #{order.id} received!")

    items = []
    for item in order.items:
        items.append(schemas.OrderItemResponse(
            id=item.id, dish_id=item.dish_id, quantity=item.quantity,
            price=item.price, dish_name=item.dish.name if item.dish else None,
        ))

    return schemas.OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        restaurant_id=order.restaurant_id,
        total_amount=order.total_amount,
        discount_amount=order.discount_amount,
        restaurant_fee=order.restaurant_fee,
        payment_mode=order.payment_mode,
        order_status=order.order_status,
        delivery_partner_id=order.delivery_partner_id,
        estimated_delivery_time=order.estimated_delivery_time,
        created_at=order.created_at,
        items=items,
        restaurant_name=rest.name,
    )


# ── Orders ───────────────────────────────────────────
@router.get("/orders", response_model=list[schemas.OrderResponse])
def my_orders(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    orders = (
        db.query(models.Order)
        .filter(models.Order.customer_id == user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )
    result = []
    for o in orders:
        items = []
        for item in o.items:
            items.append(schemas.OrderItemResponse(
                id=item.id, dish_id=item.dish_id, quantity=item.quantity,
                price=item.price, dish_name=item.dish.name if item.dish else None,
            ))
        dp_name = None
        if o.delivery_partner and o.delivery_partner.user:
            dp_name = o.delivery_partner.user.name
        result.append(schemas.OrderResponse(
            id=o.id,
            customer_id=o.customer_id,
            restaurant_id=o.restaurant_id,
            total_amount=o.total_amount,
            discount_amount=o.discount_amount,
            restaurant_fee=o.restaurant_fee,
            payment_mode=o.payment_mode,
            order_status=o.order_status,
            delivery_partner_id=o.delivery_partner_id,
            estimated_delivery_time=o.estimated_delivery_time,
            created_at=o.created_at,
            items=items,
            restaurant_name=o.restaurant.name if o.restaurant else None,
            delivery_partner_name=dp_name,
        ))
    return result


@router.get("/orders/{order_id}", response_model=schemas.OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    o = (
        db.query(models.Order)
        .filter(models.Order.id == order_id, models.Order.customer_id == user.id)
        .first()
    )
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    items = []
    for item in o.items:
        items.append(schemas.OrderItemResponse(
            id=item.id, dish_id=item.dish_id, quantity=item.quantity,
            price=item.price, dish_name=item.dish.name if item.dish else None,
        ))
    dp_name = None
    if o.delivery_partner and o.delivery_partner.user:
        dp_name = o.delivery_partner.user.name
    return schemas.OrderResponse(
        id=o.id,
        customer_id=o.customer_id,
        restaurant_id=o.restaurant_id,
        total_amount=o.total_amount,
        discount_amount=o.discount_amount,
        restaurant_fee=o.restaurant_fee,
        payment_mode=o.payment_mode,
        order_status=o.order_status,
        delivery_partner_id=o.delivery_partner_id,
        estimated_delivery_time=o.estimated_delivery_time,
        created_at=o.created_at,
        items=items,
        restaurant_name=o.restaurant.name if o.restaurant else None,
        delivery_partner_name=dp_name,
    )


# ── Reorder (Innovation Feature) ────────────────────
@router.post("/orders/{order_id}/reorder")
def reorder(
    order_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    """Reorder: adds items from a past order back to cart."""
    old_order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id, models.Order.customer_id == user.id)
        .first()
    )
    if not old_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Clear current cart
    db.query(models.Cart).filter(models.Cart.customer_id == user.id).delete()

    added = 0
    skipped = 0
    for item in old_order.items:
        dish = db.query(models.Dish).filter(models.Dish.id == item.dish_id).first()
        if dish and dish.availability:
            cart_item = models.Cart(
                customer_id=user.id,
                dish_id=dish.id,
                restaurant_id=old_order.restaurant_id,
                quantity=item.quantity,
            )
            db.add(cart_item)
            added += 1
        else:
            skipped += 1

    db.commit()
    return {
        "message": f"Reorder complete. {added} items added to cart, {skipped} unavailable items skipped.",
        "added": added,
        "skipped": skipped,
    }


# ── Complaints ───────────────────────────────────────
@router.post("/complaints", response_model=schemas.ComplaintResponse)
def raise_complaint(
    data: schemas.ComplaintCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == data.order_id, models.Order.customer_id == user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    complaint = models.Complaint(
        order_id=data.order_id,
        customer_id=user.id,
        description=data.description,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return schemas.ComplaintResponse(
        id=complaint.id,
        order_id=complaint.order_id,
        customer_id=complaint.customer_id,
        description=complaint.description,
        status=complaint.status,
        resolution_notes=complaint.resolution_notes,
        created_at=complaint.created_at,
        customer_name=user.name,
    )


@router.get("/complaints", response_model=list[schemas.ComplaintResponse])
def my_complaints(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    complaints = (
        db.query(models.Complaint)
        .filter(models.Complaint.customer_id == user.id)
        .order_by(models.Complaint.created_at.desc())
        .all()
    )
    return [
        schemas.ComplaintResponse(
            id=c.id, order_id=c.order_id, customer_id=c.customer_id,
            description=c.description, status=c.status,
            resolution_notes=c.resolution_notes, created_at=c.created_at,
            customer_name=user.name,
        )
        for c in complaints
    ]


# ── Notifications ────────────────────────────────────
@router.get("/notifications", response_model=list[schemas.NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user.id)
        .order_by(models.Notification.created_at.desc())
        .limit(20)
        .all()
    )


@router.put("/notifications/read")
def mark_notifications_read(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.Notification).filter(
        models.Notification.user_id == user.id,
        models.Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
