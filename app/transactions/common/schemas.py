from pydantic import BaseModel
from app.transactions.common.models import ContractStatus, PaymentStatus

class ContractStatusUpdate(BaseModel):
    status: ContractStatus


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
