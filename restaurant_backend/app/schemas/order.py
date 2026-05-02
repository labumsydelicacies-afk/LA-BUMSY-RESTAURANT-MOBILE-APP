#================================#
#        ORDER SCHEMAS           #
#================================#

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


# -------- ORDER ITEM CREATE --------#
class OrderItemCreate(BaseModel):
    food_id: int
    quantity: int = Field(gt=0)


# -------- ORDER ITEM RESPONSE --------#
class OrderItemResponse(BaseModel):
    food_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True


# -------- ORDER CREATE --------#
class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(min_length=1)


# -------- ORDER RESPONSE --------#
class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_price: float
    created_at: datetime
    items: List[OrderItemResponse]
    delivery_otp: str | None = None

    # Payment fields — populated after Flutterwave integration
    payment_status: str | None = None
    payment_reference: str | None = None
    paid_at: datetime | None = None
    payment_provider: str | None = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
