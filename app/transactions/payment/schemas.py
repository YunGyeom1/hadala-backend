from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class PaymentSummary(BaseModel):
    unpaid_receivables: float  # 미수금 (받아야 할 돈)
    overdue_payables: float    # 연체 지급금 (내야 할 돈 중 연체)
    prepaid_income: float      # 선수금 (미리 받은 돈)
    prepaid_expense: float     # 선지급금 (미리 낸 돈)
    total_income: float        # 총 수입 (실제 받은 돈)
    total_expense: float       # 총 지출 (실제 낸 돈)

class ContractPaymentInfo(BaseModel):
    contract_name: str
    counterparty: str
    income: float
    expense: float
    status: str
    pending_amount: float
    is_overdue: bool

class UpcomingPayment(BaseModel):
    id: str
    title: str
    counterparty: str
    amount: float
    due_date: str
    type: str  # "receivable" (받을 돈) 또는 "payable" (낼 돈)
    days_until_due: int

class PaymentReport(BaseModel):
    summary: PaymentSummary
    contracts: List[ContractPaymentInfo]
    upcoming_receivables: List[UpcomingPayment]  # 7일 내 받을 돈
    upcoming_payables: List[UpcomingPayment]     # 7일 내 낼 돈

    model_config = ConfigDict(from_attributes=True) 