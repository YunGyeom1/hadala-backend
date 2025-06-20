from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from app.transactions.common.models import ProductQuality
from enum import Enum
from uuid import UUID

class TransactionType(str, Enum):
    CONTRACT = "contract"
    SHIPMENT = "shipment"

class Direction(str, Enum):
    OUTBOUND = "outbound"  # 센터에서 나가는 것
    INBOUND = "inbound"    # 센터로 들어오는 것

class CenterItem(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: int

class CenterSummary(BaseModel):
    center_name: str
    items: List[CenterItem]

class DailySummary(BaseModel):
    date: date
    center_summaries: List[CenterSummary]


class SummaryBase(BaseModel):
    start_date: date
    end_date: date
    direction: Direction
    transaction_type: TransactionType

class SummaryResponse(SummaryBase):
    daily_summaries: List[DailySummary]

class SummaryRequest(SummaryBase):
    company_id: Optional[UUID] = None