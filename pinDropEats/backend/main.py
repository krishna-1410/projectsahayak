import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from auth import hash_password, verify_password, create_access_token, get_current_user
import models
import schemas

from routers import admin, restaurant_owner, customer, delivery, customer_care

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PinDrop Eats",
    description="Online Food Ordering & Delivery Management System",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router)
app.include_router(restaurant_owner.router)
app.include_router(customer.router)
app.include_router(delivery.router)
app.include_router(customer_care.router)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ── Auth Endpoints ───────────────────────────────────
@app.post("/api/auth/register", response_model=schemas.TokenResponse)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=data.name,
        email=data.email,
        password=hash_password(data.password),
        role=data.role,
        pin_code=data.pin_code,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto-create delivery partner profile
    if data.role == "delivery":
        dp = models.DeliveryPartner(
            user_id=user.id,
            availability=True,
            pin_code=data.pin_code,
        )
        db.add(dp)
        db.commit()

    token = create_access_token({"user_id": user.id, "role": user.role})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserResponse.model_validate(user),
    )


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id, "role": user.role})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserResponse.model_validate(user),
    )


@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_me(user: models.User = Depends(get_current_user)):
    return schemas.UserResponse.model_validate(user)


# ── Notifications (shared across roles) ──────────────
@app.get("/api/notifications", response_model=list[schemas.NotificationResponse])
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


@app.put("/api/notifications/read")
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


@app.get("/")
def root():
    return {"message": "PinDrop Eats API is running!", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
