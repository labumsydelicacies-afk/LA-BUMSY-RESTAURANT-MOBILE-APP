#================================#
#    TABLE MODEL DEFINITIONS     #
#================================#



from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base




#-----  USER MODEL  -----#
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    nickname: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rider: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    deliveries = relationship("Delivery", back_populates="rider", foreign_keys="Delivery.rider_id")
    email_verifications = relationship(
        "EmailVerification",
        back_populates="user",
        cascade="all, delete-orphan"
    )




#----- FOOD MODEL  -----#
class Food(Base):
    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    order_items = relationship("OrderItem", back_populates="food")




#----- ORDER MODEL  -----#
class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    rider_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    total_price: Mapped[float] = mapped_column(Float, default=0)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    rider = relationship("User", foreign_keys=[rider_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete")
    delivery = relationship("Delivery", back_populates="order", uselist=False)
    delivery_verification = relationship("DeliveryVerification", back_populates="order", uselist=False)




#----- ORDER ITEM MODEL  -----#
class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    food_id: Mapped[int] = mapped_column(Integer, ForeignKey("foods.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    food = relationship("Food", back_populates="order_items")




#----- EMAIL VERIFICATION MODEL  -----#
class EmailVerification(Base):
    __tablename__ = "email_verification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    code_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    user = relationship("User", back_populates="email_verifications")




#----- DELIVERY MODEL  -----#
class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    rider_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    assigned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    order = relationship("Order", back_populates="delivery")
    rider = relationship("User", back_populates="deliveries", foreign_keys=[rider_id])




#----- DELIVERY VERIFICATION (OTP) MODEL  -----#
class DeliveryVerification(Base):
    __tablename__ = "delivery_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)

    otp_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    order = relationship("Order", back_populates="delivery_verification")