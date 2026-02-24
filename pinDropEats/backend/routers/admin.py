from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from auth import require_role
import models
import schemas

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Restaurants ──────────────────────────────────────
@router.get("/restaurants", response_model=list[schemas.RestaurantResponse])
def list_all_restaurants(
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("admin")),
):
    return db.query(models.Restaurant).all()


@router.post("/restaurants", response_model=schemas.RestaurantResponse)
def add_restaurant(
    data: schemas.RestaurantCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("admin")),
):
    rest = models.Restaurant(**data.model_dump())
    db.add(rest)
    db.commit()
    db.refresh(rest)
    return rest


@router.put("/restaurants/{restaurant_id}", response_model=schemas.RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    data: schemas.RestaurantUpdate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("admin")),
):
    rest = db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()
    if not rest:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(rest, key, val)
    db.commit()
    db.refresh(rest)
    return rest


# ── Platform Offers ──────────────────────────────────
@router.get("/offers", response_model=list[schemas.OfferResponse])
def list_platform_offers(
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("admin")),
):
    return db.query(models.Offer).filter(models.Offer.applicable_type == "platform").all()


@router.post("/offers", response_model=schemas.OfferResponse)
def create_platform_offer(
    data: schemas.OfferCreate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("admin")),
):
    if data.applicable_type != "platform":
        raise HTTPException(status_code=400, detail="Admin can only create platform-level offers")
    offer = models.Offer(**data.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.delete("/offers/{offer_id}")
def delete_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("admin")),
):
    offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    db.delete(offer)
    db.commit()
    return {"message": "Offer deleted"}


# ── Statistics ───────────────────────────────────────
@router.get("/stats", response_model=schemas.PlatformStats)
def get_platform_stats(
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("admin")),
):
    total_orders = db.query(models.Order).count()
    total_revenue = db.query(func.coalesce(func.sum(models.Order.total_amount), 0)).scalar()
    total_restaurants = db.query(models.Restaurant).count()
    total_customers = db.query(models.User).filter(models.User.role == "customer").count()
    total_dp = db.query(models.DeliveryPartner).count()

    # Orders grouped by status
    status_counts = (
        db.query(models.Order.order_status, func.count(models.Order.id))
        .group_by(models.Order.order_status)
        .all()
    )
    orders_by_status = {s: c for s, c in status_counts}

    return schemas.PlatformStats(
        total_orders=total_orders,
        total_revenue=float(total_revenue),
        total_restaurants=total_restaurants,
        total_customers=total_customers,
        total_delivery_partners=total_dp,
        orders_by_status=orders_by_status,
    )
