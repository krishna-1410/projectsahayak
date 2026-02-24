from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import require_role, create_notification
import models
import schemas

router = APIRouter(prefix="/api/owner", tags=["Restaurant Owner"])

VALID_OWNER_TRANSITIONS = {
    "Placed": ["Accepted", "Rejected"],
    "Accepted": ["Preparing"],
    "Preparing": ["Out for Delivery"],
}


def _get_owner_restaurant(db: Session, user: models.User) -> models.Restaurant:
    rest = db.query(models.Restaurant).filter(models.Restaurant.owner_id == user.id).first()
    if not rest:
        raise HTTPException(status_code=404, detail="No restaurant linked to your account")
    return rest


# ── Dishes ───────────────────────────────────────────
@router.get("/dishes", response_model=list[schemas.DishResponse])
def list_my_dishes(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    rest = _get_owner_restaurant(db, user)
    return db.query(models.Dish).filter(models.Dish.restaurant_id == rest.id).all()


@router.post("/dishes", response_model=schemas.DishResponse)
def add_dish(
    data: schemas.DishCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    rest = _get_owner_restaurant(db, user)
    if data.restaurant_id != rest.id:
        raise HTTPException(status_code=403, detail="You can only add dishes to your own restaurant")
    dish = models.Dish(**data.model_dump())
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish


@router.put("/dishes/{dish_id}", response_model=schemas.DishResponse)
def update_dish(
    dish_id: int,
    data: schemas.DishUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    rest = _get_owner_restaurant(db, user)
    dish = (
        db.query(models.Dish)
        .filter(models.Dish.id == dish_id, models.Dish.restaurant_id == rest.id)
        .first()
    )
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found in your restaurant")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(dish, key, val)
    db.commit()
    db.refresh(dish)
    return dish


@router.delete("/dishes/{dish_id}")
def remove_dish(
    dish_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    rest = _get_owner_restaurant(db, user)
    dish = (
        db.query(models.Dish)
        .filter(models.Dish.id == dish_id, models.Dish.restaurant_id == rest.id)
        .first()
    )
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found in your restaurant")
    db.delete(dish)
    db.commit()
    return {"message": "Dish removed"}


# ── Orders ───────────────────────────────────────────
@router.get("/orders", response_model=list[schemas.OrderResponse])
def list_restaurant_orders(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    rest = _get_owner_restaurant(db, user)
    orders = (
        db.query(models.Order)
        .filter(models.Order.restaurant_id == rest.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )
    result = []
    for o in orders:
        items = []
        for item in o.items:
            items.append(schemas.OrderItemResponse(
                id=item.id,
                dish_id=item.dish_id,
                quantity=item.quantity,
                price=item.price,
                dish_name=item.dish.name if item.dish else None,
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
            restaurant_name=rest.name,
            customer_name=o.customer.name if o.customer else None,
        ))
    return result


@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    data: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    rest = _get_owner_restaurant(db, user)
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id, models.Order.restaurant_id == rest.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    current = order.order_status
    new_status = data.status
    allowed = VALID_OWNER_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current}' to '{new_status}'. Allowed: {allowed}",
        )

    # If transitioning to Out for Delivery, assign a delivery partner
    if new_status == "Out for Delivery":
        partner = (
            db.query(models.DeliveryPartner)
            .filter(
                models.DeliveryPartner.availability == True,
                models.DeliveryPartner.pin_code == rest.pin_code,
            )
            .first()
        )
        if not partner:
            raise HTTPException(
                status_code=400,
                detail="No delivery partner available in this area. Cannot send for delivery.",
            )
        order.delivery_partner_id = partner.id
        partner.availability = False
        # Notify delivery partner
        create_notification(db, partner.user_id, f"New delivery assigned! Order #{order.id}")

    order.order_status = new_status
    db.commit()

    # Notify customer
    create_notification(
        db, order.customer_id,
        f"Order #{order.id} status updated to: {new_status}"
    )

    return {"message": f"Order status updated to '{new_status}'"}


# ── Restaurant Offers ────────────────────────────────
@router.get("/offers", response_model=list[schemas.OfferResponse])
def list_restaurant_offers(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    rest = _get_owner_restaurant(db, user)
    return (
        db.query(models.Offer)
        .filter(models.Offer.restaurant_id == rest.id, models.Offer.applicable_type == "restaurant")
        .all()
    )


@router.post("/offers", response_model=schemas.OfferResponse)
def create_restaurant_offer(
    data: schemas.OfferCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    rest = _get_owner_restaurant(db, user)
    if data.applicable_type != "restaurant":
        raise HTTPException(status_code=400, detail="Restaurant owners create restaurant-level offers only")
    offer = models.Offer(**data.model_dump())
    offer.restaurant_id = rest.id
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/restaurant", response_model=schemas.RestaurantResponse)
def get_my_restaurant(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("owner")),
):
    return _get_owner_restaurant(db, user)
