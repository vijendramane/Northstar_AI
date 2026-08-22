
from typing import Optional
from pydantic import BaseModel


class CustomerProfileUpdate(BaseModel):
    name: Optional[str] = None
    configuration: Optional[str] = None
    budget: Optional[str] = None
    purpose: Optional[str] = None
    timeline: Optional[str] = None
    location_preference: Optional[str] = None
    preferred_language: Optional[str] = None
    interest_level: Optional[str] = None
    objection: Optional[str] = None

    # NEW
    intent: Optional[str] = None