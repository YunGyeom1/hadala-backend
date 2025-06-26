from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from uuid import UUID
from datetime import datetime, date, timedelta
from typing import List, Optional
from app.transactions.contract.models import Contract
from app.transactions.common.models import PaymentStatus
from app.profile.models import Profile
from app.company.common.models import Company
from . import schemas

def get_payment_report(
    db: Session, 
    company_id: UUID, 
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> schemas.PaymentReport:
    """
    회사의 지급 현황 보고서를 생성합니다.
    """
    # 회사와 관련된 모든 계약 조회 (공급자 또는 수신자)
    query = db.query(Contract).options(
        joinedload(Contract.supplier_company),
        joinedload(Contract.receiver_company),
        joinedload(Contract.supplier_contractor),
        joinedload(Contract.receiver_contractor)
    ).filter(
        or_(
            Contract.supplier_company_id == company_id,
            Contract.receiver_company_id == company_id
        )
    )
    
    # 날짜 필터 적용
    if start_date:
        query = query.filter(Contract.contract_datetime >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Contract.contract_datetime <= datetime.combine(end_date, datetime.max.time()))
    
    contracts = query.all()
    
    # 요약 통계 계산
    unpaid_receivables = 0.0  # 미수금 (받아야 할 돈)
    overdue_payables = 0.0    # 연체 지급금 (내야 할 돈 중 연체)
    prepaid_income = 0.0      # 선수금 (미리 받은 돈)
    prepaid_expense = 0.0     # 선지급금 (미리 낸 돈)
    total_income = 0.0        # 총 수입 (실제 받은 돈)
    total_expense = 0.0       # 총 지출 (실제 낸 돈)
    
    contract_payments = []
    upcoming_receivables = []
    upcoming_payables = []
    
    today = date.today()
    seven_days_later = today + timedelta(days=7)
    
    for contract in contracts:
        # 계약이 우리 회사에 유리한지 판단 (수입 > 지출)
        is_income_contract = False
        if contract.supplier_company_id == company_id:
            # 우리가 공급자 (수입 계약)
            is_income_contract = True
            income = contract.total_price
            expense = 0.0
            counterparty = contract.receiver_company.name if contract.receiver_company else "미지정"
        else:
            # 우리가 수신자 (지출 계약)
            is_income_contract = False
            income = 0.0
            expense = contract.total_price
            counterparty = contract.supplier_company.name if contract.supplier_company else "미지정"
        
        # 결제 상태에 따른 분류
        status = contract.payment_status.value
        pending_amount = 0.0
        is_overdue = False
        
        if is_income_contract:
            # 수입 계약
            if status == "unpaid":
                pending_amount = income
                unpaid_receivables += income
            elif status == "paid":
                pending_amount = 0.0
                total_income += income  # 실제 받은 돈
            elif status == "prepared":
                pending_amount = 0.0
                prepaid_income += income
        else:
            # 지출 계약
            if status == "unpaid":
                pending_amount = expense
                # 연체 여부 확인
                if contract.payment_due_date and contract.payment_due_date.date() < today:
                    is_overdue = True
                    overdue_payables += expense
            elif status == "paid":
                pending_amount = 0.0
                total_expense += expense  # 실제 낸 돈
            elif status == "prepared":
                pending_amount = 0.0
                prepaid_expense += expense
        
        # 임박 목록 확인 (7일 내)
        if contract.payment_due_date:
            due_date = contract.payment_due_date.date()
            if today <= due_date <= seven_days_later and status == "unpaid":
                days_until_due = (due_date - today).days
                
                upcoming_payment = schemas.UpcomingPayment(
                    id=str(contract.id),
                    title=contract.title,
                    counterparty=counterparty,
                    amount=contract.total_price,
                    due_date=due_date.isoformat(),
                    type="receivable" if is_income_contract else "payable",
                    days_until_due=days_until_due
                )
                
                if is_income_contract:
                    upcoming_receivables.append(upcoming_payment)
                else:
                    upcoming_payables.append(upcoming_payment)
        
        contract_payments.append(schemas.ContractPaymentInfo(
            contract_name=contract.title,
            counterparty=counterparty,
            income=income,
            expense=expense,
            status=status,
            pending_amount=pending_amount,
            is_overdue=is_overdue
        ))
    
    # 임박 목록을 날짜순으로 정렬
    upcoming_receivables.sort(key=lambda x: x.days_until_due)
    upcoming_payables.sort(key=lambda x: x.days_until_due)
    
    # 요약 정보 생성
    summary = schemas.PaymentSummary(
        unpaid_receivables=unpaid_receivables,
        overdue_payables=overdue_payables,
        prepaid_income=prepaid_income,
        prepaid_expense=prepaid_expense,
        total_income=total_income,
        total_expense=total_expense
    )
    
    return schemas.PaymentReport(
        summary=summary,
        contracts=contract_payments,
        upcoming_receivables=upcoming_receivables,
        upcoming_payables=upcoming_payables
    )

def get_company_payment_summary(
    db: Session, 
    company_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> schemas.PaymentSummary:
    """
    회사의 지급 현황 요약만 반환합니다.
    """
    report = get_payment_report(db, company_id, start_date, end_date)
    return report.summary

def get_overdue_contracts(db: Session, company_id: UUID) -> List[Contract]:
    """
    연체된 계약 목록을 반환합니다.
    """
    return db.query(Contract).filter(
        and_(
            Contract.receiver_company_id == company_id,  # 우리가 수신자 (지출 계약)
            Contract.payment_status == PaymentStatus.UNPAID,
            Contract.payment_due_date < datetime.now()
        )
    ).all() 