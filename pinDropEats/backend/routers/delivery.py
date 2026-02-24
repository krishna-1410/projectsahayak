from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import require_role, create_notification
import models
import schemas

router = APIRouter(prefix="/api/delivery", tags=["Delivery Partner"])


def _get_partner(db: Session, user: models.User) -> models.DeliveryPartner:
    partner = (
        db.query(models.DeliveryPartner)
        .filter(models.DeliveryPartner.user_id == user.id)
        .first()
    )
    if not partner:
        raise HTTPException(status_code=404, detail="Delivery partner profile not found")
    return partner


# ── Availability Toggle ──────────────────────────────
@router.put("/availability")
def toggle_availability(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("delivery")),
):
    partner = _get_partner(db, user)
    partner.availability = not partner.availability
    db.commit()
    status = "available" if partner.availability else "offline"
    return {"message": f"You are now {status}", "availability": partner.availability}


@router.get("/status", response_model=schemas.DeliveryPartnerResponse)
def get_my_status(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("delivery")),
):
    partner = _get_partner(db, user)
    return schemas.DeliveryPartnerResponse(
        id=partner.id,
        user_id=partner.user_id,
        availability=partner.availability,
        pin_code=partner.pin_code,
        name=user.name,
    )


# ── Assigned Orders ──────────────────────────────────
@router.get("/orders", response_model=list[schemas.OrderResponse])
def get_assigned_orders(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("delivery")),
):
    partner = _get_partner(db, user)
    orders = (
        db.query(models.Order)
        .filter(models.Order.delivery_partner_id == partner.id)
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
            customer_name=o.customer.name if o.customer else None,
        ))
    return result


# ── Mark Delivered ───────────────────────────────────
@router.put("/orders/{order_id}/deliver")
def mark_delivered(
    order_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("delivery")),
):
    partner = _get_partner(db, user)
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id, models.Order.delivery_partner_id == partner.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not assigned to you")

    if order.order_status != "Out for Delivery":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mark as delivered. Current status: '{order.order_status}'. Must be 'Out for Delivery'.",
        )

    order.order_status = "Delivered"
    partner.availability = True  # Free up the delivery partner
    db.commit()

    # Notify customer
    create_notification(
        db, order.customer_id,
        f"Order #{order.id} has been delivered! Enjoy your meal! 🍽️"
    )

    return {"message": "Order marked as delivered"}
