from pydantic import BaseModel
from datetime import date
from typing import List
from app.transactions.common.models import ProductQuality

class ShipmentSummaryRow(BaseModel):
    shipment_date: date
    center_name: str
    product_name: str
    shipment_type: str
    quality: ProductQuality
    quantity: int
    destination: str

class ShipmentSummary(BaseModel):
    rows: List[ShipmentSummaryRow]