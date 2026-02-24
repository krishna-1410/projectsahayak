from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import require_role, create_notification
import models
import schemas

router = APIRouter(prefix="/api/care", tags=["Customer Care"])


# ── Complaints ───────────────────────────────────────
@router.get("/complaints", response_model=list[schemas.ComplaintResponse])
def list_all_complaints(
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("care")),
):
    complaints = (
        db.query(models.Complaint)
        .order_by(models.Complaint.created_at.desc())
        .all()
    )
    result = []
    for c in complaints:
        cust = db.query(models.User).filter(models.User.id == c.customer_id).first()
        result.append(schemas.ComplaintResponse(
            id=c.id,
            order_id=c.order_id,
            customer_id=c.customer_id,
            description=c.description,
            status=c.status,
            resolution_notes=c.resolution_notes,
            created_at=c.created_at,
            customer_name=cust.name if cust else None,
        ))
    return result


@router.put("/complaints/{complaint_id}", response_model=schemas.ComplaintResponse)
def update_complaint(
    complaint_id: int,
    data: schemas.ComplaintUpdate,
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("care")),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if data.status:
        allowed_statuses = ["Open", "In Progress", "Resolved", "Closed"]
        if data.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Status must be one of: {allowed_statuses}",
            )
        complaint.status = data.status

    if data.resolution_notes:
        complaint.resolution_notes = data.resolution_notes

    db.commit()
    db.refresh(complaint)

    # Notify customer about complaint update
    create_notification(
        db, complaint.customer_id,
        f"Complaint #{complaint.id} updated to: {complaint.status}"
    )

    cust = db.query(models.User).filter(models.User.id == complaint.customer_id).first()
    return schemas.ComplaintResponse(
        id=complaint.id,
        order_id=complaint.order_id,
        customer_id=complaint.customer_id,
        description=complaint.description,
        status=complaint.status,
        resolution_notes=complaint.resolution_notes,
        created_at=complaint.created_at,
        customer_name=cust.name if cust else None,
    )


# ── Cancel Order ─────────────────────────────────────
@router.put("/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("care")),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    non_cancellable = ["Delivered", "Cancelled", "Rejected"]
    if order.order_status in non_cancellable:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order.order_status}'",
        )

    order.order_status = "Cancelled"

    # Free up delivery partner if assigned
    if order.delivery_partner_id:
        partner = (
            db.query(models.DeliveryPartner)
            .filter(models.DeliveryPartner.id == order.delivery_partner_id)
            .first()
        )
        if partner:
            partner.availability = True

    db.commit()

    # Notify customer
    create_notification(
        db, order.customer_id,
        f"Order #{order.id} has been cancelled by customer care."
    )

    return {"message": f"Order #{order_id} cancelled successfully"}


# ── View Orders (for reference during complaints) ────
@router.get("/orders", response_model=list[schemas.OrderResponse])
def list_all_orders(
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_role("care")),
):
    orders = (
        db.query(models.Order)
        .order_by(models.Order.created_at.desc())
        .limit(100)
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
            customer_name=o.customer.name if o.customer else None,
            delivery_partner_name=dp_name,
        ))
    return result
