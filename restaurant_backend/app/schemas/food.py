#================================#
#    ADMIN  FOOD SCHEMAS         #
#================================#

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


#base class that defines the common fields for food items
class FoodBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    image_url: Optional[str] = None
    is_available: bool = True


class FoodCreate(FoodBase):
    pass


#this intentionally didnt inherit from foodbase
#because updates are partial and all fields are optional
class FoodUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = None
    is_available: Optional[bool] = None


class FoodResponse(FoodBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True