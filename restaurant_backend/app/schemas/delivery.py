#=================================#
#        DELIVERY SCHEMAS          #
#=================================#

from datetime import datetime

from pydantic import BaseModel

from app.schemas.order import OrderResponse


# ─── Request schemas ─────────────────────────────────────────────────────────

class DeliveryAcceptRequest(BaseModel):
    order_id: int


class DeliveryCompleteRequest(BaseModel):
    order_id: int
    otp: str


# ─── Response schemas ─────────────────────────────────────────────────────────

class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    rider_id: int
    assigned_at: datetime
    picked_up_at: datetime | None
    delivered_at: datetime | None
    notes: str | None

    class Config:
        from_attributes = True


class DeliveryWithOrderResponse(DeliveryResponse):
    order: OrderResponse

    class Config:
        from_attributes = True


class AvailableOrderResponse(OrderResponse):
    """Order visible to riders on the available-orders feed."""
    pass
