from uuid import uuid4
from sqlalchemy.orm import Session
from app.profile.models import User
from app.core.auth.utils import create_access_token, create_refresh_token
from app.profiles.wholesaler.models import Wholesaler
from app.wholesale_company.company.models import Company
from app.profiles.farmer.models import Farmer
from app.profiles.retailer.models import Retailer
from app.wholesale_company.center.models import Center
from app.profiles.wholesaler.models import Wholesaler
from app.wholesale_company.inventory.models import CompanyCropInventory, CompanyCropInventoryItem
from datetime import date, timedelta
from uuid import UUID
from typing import Optional
from app.transactions.wholesale_contract.models import WholesaleContract, WholesaleContractItem, ContractStatus, PaymentStatus
from app.transactions.retail_contract.models import RetailContract, RetailContractItem

def create_user(
    db: Session,
    name: str = "Test User",
    email_prefix: str = "test",
    oauth_provider: str = "google",
    oauth_sub: str = None
) -> User:
    user = User(
        email=f"{email_prefix}{uuid4()}@example.com",
        name=name,
        oauth_provider=oauth_provider,
        oauth_sub=oauth_sub or str(uuid4())
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_token_pair(user: User):
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return access_token, refresh_token


def create_wholesaler(
    db: Session,
    user: User,
    name: str = "테스트 도매상",
    phone: str = "010-1234-5678",
    role: str = "owner"
) -> Wholesaler:
    wholesaler = Wholesaler(
        user_id=user.id,
        name=name,
        phone=phone,
        role=role
    )
    db.add(wholesaler)
    db.commit()
    db.refresh(wholesaler)
    return wholesaler

def add_company_wholesaler(
    db: Session,
    wholesaler: Wholesaler,
    company: Company
) -> Wholesaler:
    wholesaler.company_id = company.id
    db.commit()
    db.refresh(wholesaler)
    return wholesaler

def create_farmer(
    db: Session,
    user_id: Optional[str] = None,
    name: str = "테스트농부",
    address : str = "경기도 남양주시",
    farm_size_m2: float = 1200.0,
    annual_output_kg: float = 2000.0,
    farm_members: int = 4
) -> Farmer:
    farmer = Farmer(
        name=name,
        address=address,
        farm_size_m2=farm_size_m2,
        annual_output_kg=annual_output_kg,
        farm_members=farm_members,
        user_id=user_id
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer


def create_retailer(
    db: Session,
    user_id: str,
    name: str = "테스트마트",
    address: str = "서울시 강남구",
    description: str = "신선식품 전문 마트"
) -> Retailer:
    retailer = Retailer(
        name=name,
        address=address,
        description=description,
        user_id=user_id
    )
    db.add(retailer)
    db.commit()
    db.refresh(retailer)
    return retailer

def create_center(
    db: Session,
    company_id: str,
    name: str = "테스트 센터",
    address: str = "서울시 송파구"
) -> Center:
    center = Center(
        id=uuid4(),
        name=name,
        address=address,
        company_id=company_id
    )
    db.add(center)
    db.commit()
    db.refresh(center)
    return center


def create_company(
    db: Session,
    user_id: str,
    name: str = "테스트 회사",
    description: str = "테스트 회사 설명",
    business_number: str = None,
    address: str = "서울시 강남구",
    phone: str = "02-1234-5678",
    email_prefix: str = "test"
) -> Company:
    # 1. 해당 유저의 wholesaler 레코드 조회
    wholesaler = db.query(Wholesaler).filter(Wholesaler.user_id == user_id).first()
    if not wholesaler:
        raise ValueError("Wholesaler not found for given user_id")

    # 2. 회사 생성 (owner는 wholesaler.id)
    company = Company(
        name=name,
        description=description,
        business_number=business_number or "3",
        address=address,
        phone=phone,
        email=f"{email_prefix}{uuid4()}@company.com",
        owner=wholesaler.id 
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    # 3. 도매상에 company_id 및 role 연결
    wholesaler.company_id = company.id
    wholesaler.role = "owner"
    db.commit()
    db.refresh(wholesaler)

    return company
    
def create_inventory(db: Session, company_id: UUID, center_id: UUID, snapshot_date: date = date.today()):
    inventory = CompanyCropInventory(
        id=str(uuid4()),
        date=snapshot_date,
        company_id=str(company_id),
        center_id=str(center_id)
    )
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory


def create_inventory_item(db: Session, inventory_id: UUID, crop_name: str = "상추", quality_grade: str = "A", quantity: float = 10.0):
    item = CompanyCropInventoryItem(
        id=str(uuid4()),
        inventory_id=str(inventory_id),
        crop_name=crop_name,
        quality_grade=quality_grade,
        quantity=quantity
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def fake_user_id():
    return str(uuid4())

def create_wholesale_contract(
    db: Session,
    center_id: UUID,
    wholesaler_id: UUID,
    farmer_id: UUID,
    company_id: UUID,
    contract_date: date = None,
    shipment_date: date = None,
    status: ContractStatus = ContractStatus.DRAFT,
    payment_status: PaymentStatus = PaymentStatus.PENDING
) -> WholesaleContract:
    """테스트용 도매 계약을 생성합니다."""
    if contract_date is None:
        contract_date = date.today()
    if shipment_date is None:
        shipment_date = contract_date + timedelta(days=7)

    contract = WholesaleContract(
        center_id=center_id,
        wholesaler_id=wholesaler_id,
        farmer_id=farmer_id,
        company_id=company_id,
        contract_date=contract_date,
        shipment_date=shipment_date,
        contract_status=status,
        payment_status=payment_status,
        note="테스트 계약"
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract

def create_wholesale_contract_item(
    db: Session,
    contract_id: UUID,
    crop_name: str = "사과",
    quantity_kg: float = 100.0,
    unit_price: float = 5000.0,
    quality_required: str = "A"
) -> WholesaleContractItem:
    """테스트용 도매 계약 품목을 생성합니다."""
    item = WholesaleContractItem(
        contract_id=contract_id,
        crop_name=crop_name,
        quantity_kg=quantity_kg,
        unit_price=unit_price,
        total_price=quantity_kg * unit_price,
        quality_required=quality_required
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item



def create_retail_contract(
    db: Session,
    company_id,
    wholesaler_id,
    retailer_id,
    center_id,
    contract_date=None,
    shipment_date=None,
    note: str = "기본 비고"
) -> RetailContract:
    contract = RetailContract(
        id=uuid4(),
        company_id=company_id,
        wholesaler_id=wholesaler_id,
        retailer_id=retailer_id,
        center_id=center_id,
        contract_date=contract_date or date.today(),
        shipment_date=shipment_date or date.today(),
        note=note
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def create_retail_contract_item(
    db: Session,
    contract_id,
    crop_name: str = "감자",
    quantity_kg: float = 10.0,
    unit_price: float = 1000.0,
    quality_required: str = "A"
) -> RetailContractItem:
    item = RetailContractItem(
        id=uuid4(),
        contract_id=contract_id,
        crop_name=crop_name,
        quantity_kg=quantity_kg,
        unit_price=unit_price,
        total_price=quantity_kg * unit_price,
        quality_required=quality_required
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item