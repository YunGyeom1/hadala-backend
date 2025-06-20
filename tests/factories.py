import uuid
from datetime import datetime, timedelta, date
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.auth.models import User
from app.profile.models import Profile, ProfileType, ProfileRole
from app.company.common.models import Company, CompanyType


class UserFactory:
    @staticmethod
    def create_user(
        db: Session,
        oauth_provider: str = "google",
        oauth_sub: Optional[str] = None,
        picture_url: str = "https://example.com/picture.jpg",
        **kwargs
    ) -> User:
        """사용자를 생성합니다."""
        if oauth_sub is None:
            oauth_sub = str(uuid.uuid4())
        
        user = User(
            oauth_provider=oauth_provider,
            oauth_sub=oauth_sub,
            picture_url=picture_url,
            **kwargs
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_google_user(
        db: Session,
        oauth_sub: Optional[str] = None,
        picture_url: str = "https://google.com/picture.jpg",
        **kwargs
    ) -> User:
        """Google OAuth 사용자를 생성합니다."""
        return UserFactory.create_user(
            db, oauth_provider="google", oauth_sub=oauth_sub, picture_url=picture_url, **kwargs
        )

    @staticmethod
    def create_kakao_user(
        db: Session,
        oauth_sub: Optional[str] = None,
        picture_url: str = "https://kakao.com/picture.jpg",
        **kwargs
    ) -> User:
        """Kakao OAuth 사용자를 생성합니다."""
        return UserFactory.create_user(
            db, oauth_provider="kakao", oauth_sub=oauth_sub, picture_url=picture_url, **kwargs
        )

    @staticmethod
    def create_multiple_users(
        db: Session,
        count: int = 3,
        prefix: str = "user",
        **kwargs
    ) -> List[User]:
        """여러 사용자를 생성합니다."""
        users = []
        for i in range(count):
            user = UserFactory.create_user(
                db,
                oauth_sub=f"{prefix}_{i}_{uuid.uuid4()}",
                **kwargs
            )
            users.append(user)
        return users


class ProfileFactory:
    @staticmethod
    def create_profile(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        username: str = "testuser",
        name: str = "테스트 사용자",
        phone: str = "010-1234-5678",
        email: str = "test@example.com",
        role: ProfileRole = ProfileRole.owner,
        type: ProfileType = ProfileType.wholesaler,
        company_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> Profile:
        """프로필을 생성합니다."""
        if user_id is None:
            user = UserFactory.create_user(db)
            user_id = user.id
        
        profile = Profile(
            user_id=user_id,
            username=username,
            name=name,
            phone=phone,
            email=email,
            role=role,
            type=type,
            company_id=company_id,
            **kwargs
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_wholesaler_profile(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        username: str = "wholesaler_user",
        name: str = "도매상 사용자",
        role: ProfileRole = ProfileRole.owner,
        **kwargs
    ) -> Profile:
        """도매상 프로필을 생성합니다."""
        return ProfileFactory.create_profile(
            db, user_id=user_id, username=username, name=name,
            type=ProfileType.wholesaler, role=role, **kwargs
        )

    @staticmethod
    def create_retailer_profile(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        username: str = "retailer_user",
        name: str = "소매상 사용자",
        role: ProfileRole = ProfileRole.owner,
        **kwargs
    ) -> Profile:
        """소매상 프로필을 생성합니다."""
        return ProfileFactory.create_profile(
            db, user_id=user_id, username=username, name=name,
            type=ProfileType.retailer, role=role, **kwargs
        )

    @staticmethod
    def create_farmer_profile(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        username: str = "farmer_user",
        name: str = "농부 사용자",
        role: ProfileRole = ProfileRole.owner,
        **kwargs
    ) -> Profile:
        """농부 프로필을 생성합니다."""
        return ProfileFactory.create_profile(
            db, user_id=user_id, username=username, name=name,
            type=ProfileType.farmer, role=role, **kwargs
        )

    @staticmethod
    def create_external_profile(
        db: Session,
        username: str = "external_user",
        name: str = "외부 사용자",
        type: ProfileType = ProfileType.wholesaler,
        role: ProfileRole = ProfileRole.member,
        company_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> Profile:
        """외부 프로필을 생성합니다 (user_id가 없는 경우)."""
        profile = Profile(
            user_id=None,
            username=username,
            name=name,
            type=type,
            role=role,
            company_id=company_id,
            **kwargs
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_multiple_profiles(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        count: int = 3,
        prefix: str = "profile",
        type: ProfileType = ProfileType.wholesaler,
        **kwargs
    ) -> List[Profile]:
        """여러 프로필을 생성합니다."""
        profiles = []
        for i in range(count):
            profile = ProfileFactory.create_profile(
                db,
                user_id=user_id,
                username=f"{prefix}_{i}",
                name=f"{prefix} 사용자 {i}",
                type=type,
                **kwargs
            )
            profiles.append(profile)
        return profiles

    @staticmethod
    def create_profiles_for_user(
        db: Session,
        user_id: uuid.UUID,
        profile_types: List[ProfileType] = None,
        **kwargs
    ) -> List[Profile]:
        """사용자에게 여러 타입의 프로필을 생성합니다."""
        if profile_types is None:
            profile_types = [ProfileType.wholesaler, ProfileType.retailer, ProfileType.farmer]
        
        profiles = []
        for i, profile_type in enumerate(profile_types):
            profile = ProfileFactory.create_profile(
                db,
                user_id=user_id,
                username=f"user_{profile_type.value}_{i}",
                name=f"{profile_type.value} 사용자",
                type=profile_type,
                **kwargs
            )
            profiles.append(profile)
        return profiles


class CompanyFactory:
    @staticmethod
    def create_company(
        db: Session,
        name: str = "테스트 회사",
        type: CompanyType = CompanyType.wholesaler,
        owner_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> Company:
        """회사를 생성합니다."""
        if owner_id is None:
            # CompanyType을 ProfileType으로 변환
            profile_type_map = {
                CompanyType.wholesaler: ProfileType.wholesaler,
                CompanyType.retailer: ProfileType.retailer,
                CompanyType.farmer: ProfileType.farmer
            }
            profile_type = profile_type_map[type]
            profile = ProfileFactory.create_profile(db, type=profile_type)
            owner_id = profile.user_id
        
        company = Company(
            name=name,
            type=type,
            owner_id=owner_id,
            **kwargs
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return company

    @staticmethod
    def create_wholesale_company(
        db: Session,
        name: str = "도매 회사",
        owner_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> Company:
        """도매 회사를 생성합니다."""
        return CompanyFactory.create_company(
            db, name=name, type=CompanyType.wholesaler, owner_id=owner_id, **kwargs
        )

    @staticmethod
    def create_retail_company(
        db: Session,
        name: str = "소매 회사",
        owner_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> Company:
        """소매 회사를 생성합니다."""
        return CompanyFactory.create_company(
            db, name=name, type=CompanyType.retailer, owner_id=owner_id, **kwargs
        )

    @staticmethod
    def create_farmer_company(
        db: Session,
        name: str = "농장",
        owner_id: Optional[uuid.UUID] = None,
        **kwargs
    ) -> Company:
        """농장을 생성합니다."""
        return CompanyFactory.create_company(
            db, name=name, type=CompanyType.farmer, owner_id=owner_id, **kwargs
        )

    @staticmethod
    def create_multiple_companies(
        db: Session,
        count: int = 3,
        prefix: str = "company",
        type: CompanyType = CompanyType.wholesaler,
        **kwargs
    ) -> List[Company]:
        """여러 회사를 생성합니다."""
        companies = []
        for i in range(count):
            company = CompanyFactory.create_company(
                db,
                name=f"{prefix} {i}",
                type=type,
                **kwargs
            )
            companies.append(company)
        return companies


class TestDataFactory:
    """테스트 데이터 생성을 위한 편의 클래스"""
    
    @staticmethod
    def create_complete_user_setup(
        db: Session,
        username: str = "complete_user",
        company_name: str = "완전한 회사",
        profile_type: ProfileType = ProfileType.wholesaler,
        company_type: CompanyType = CompanyType.wholesaler,
        role: ProfileRole = ProfileRole.owner,
        **kwargs
    ) -> dict:
        """사용자, 프로필, 회사를 모두 생성하는 완전한 설정을 만듭니다."""
        # role을 kwargs에서 제거하여 User 생성 시 전달되지 않도록 함
        user_kwargs = {k: v for k, v in kwargs.items() if k != 'role'}
        user = UserFactory.create_user(db, **user_kwargs)
        company = CompanyFactory.create_company(
            db, name=company_name, type=company_type, owner_id=user.id
        )
        profile = ProfileFactory.create_profile(
            db, user_id=user.id, username=username, type=profile_type,
            company_id=company.id, role=role
        )
        # 연결 보장: company.owner_id, profile.company_id
        company.owner_id = user.id
        profile.company_id = company.id
        db.commit()
        
        return {
            "user": user,
            "profile": profile,
            "company": company
        }

    @staticmethod
    def create_multiple_complete_setups(
        db: Session,
        count: int = 3,
        prefix: str = "setup",
        **kwargs
    ) -> List[dict]:
        """여러 완전한 설정을 생성합니다."""
        setups = []
        for i in range(count):
            setup = TestDataFactory.create_complete_user_setup(
                db,
                username=f"{prefix}_{i}",
                company_name=f"{prefix} 회사 {i}",
                **kwargs
            )
            setups.append(setup)
        return setups

    @staticmethod
    def create_wholesale_ecosystem(
        db: Session,
        wholesaler_count: int = 2,
        retailer_count: int = 3,
        farmer_count: int = 4,
        **kwargs
    ) -> dict:
        """도매-소매-농부 생태계를 생성합니다."""
        # 도매상들 생성
        wholesalers = []
        for i in range(wholesaler_count):
            setup = TestDataFactory.create_complete_user_setup(
                db,
                username=f"wholesaler_{i}",
                company_name=f"도매 회사 {i}",
                profile_type=ProfileType.wholesaler,
                company_type=CompanyType.wholesaler,
                **kwargs
            )
            wholesalers.append(setup)
        
        # 소매상들 생성
        retailers = []
        for i in range(retailer_count):
            setup = TestDataFactory.create_complete_user_setup(
                db,
                username=f"retailer_{i}",
                company_name=f"소매 회사 {i}",
                profile_type=ProfileType.retailer,
                company_type=CompanyType.retailer,
                **kwargs
            )
            retailers.append(setup)
        
        # 농부들 생성
        farmers = []
        for i in range(farmer_count):
            setup = TestDataFactory.create_complete_user_setup(
                db,
                username=f"farmer_{i}",
                company_name=f"농장 {i}",
                profile_type=ProfileType.farmer,
                company_type=CompanyType.farmer,
                **kwargs
            )
            farmers.append(setup)
        
        return {
            "wholesalers": wholesalers,
            "retailers": retailers,
            "farmers": farmers
        }


class CenterFactory:
    @staticmethod
    def create_center(
        db: Session,
        company_id: uuid.UUID,
        name: str = "테스트 센터",
        address: str = "서울시 강남구",
        region: str = "강남",
        phone: str = "02-1234-5678",
        **kwargs
    ):
        """센터를 생성합니다."""
        from app.company.center.models import Center
        
        center = Center(
            name=name,
            company_id=company_id,
            address=address,
            region=region,
            phone=phone,
            **kwargs
        )
        db.add(center)
        db.commit()
        db.refresh(center)
        return center

    @staticmethod
    def create_multiple_centers(
        db: Session,
        company_id: uuid.UUID,
        count: int = 3,
        prefix: str = "센터",
        **kwargs
    ) -> List:
        """여러 센터를 생성합니다."""
        centers = []
        for i in range(count):
            center = CenterFactory.create_center(
                db,
                company_id=company_id,
                name=f"{prefix} {i+1}",
                **kwargs
            )
            centers.append(center)
        return centers


class InventorySnapshotFactory:
    @staticmethod
    def create_center_inventory_snapshot(
        db: Session,
        snapshot_date: date,
        company_id: uuid.UUID,
        center_id: uuid.UUID,
        total_quantity: int = 100,
        total_price: float = 1000000.0,
        finalized: bool = False,
        **kwargs
    ):
        """센터 재고 스냅샷을 생성합니다."""
        from app.company.inventory_snapshot.models import CenterInventorySnapshot
        
        snapshot = CenterInventorySnapshot(
            snapshot_date=snapshot_date,
            company_id=company_id,
            center_id=center_id,
            total_quantity=total_quantity,
            total_price=total_price,
            finalized=finalized,
            **kwargs
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def create_center_inventory_snapshot_item(
        db: Session,
        center_inventory_snapshot_id: uuid.UUID,
        product_name: str = "쌀",
        quantity: int = 50,
        quality: str = "A",
        unit_price: float = 10000.0,
        total_price: float = 500000.0,
        **kwargs
    ):
        """센터 재고 스냅샷 아이템을 생성합니다."""
        from app.company.inventory_snapshot.models import CenterInventorySnapshotItem
        
        item = CenterInventorySnapshotItem(
            center_inventory_snapshot_id=center_inventory_snapshot_id,
            product_name=product_name,
            quantity=quantity,
            quality=quality,
            unit_price=unit_price,
            total_price=total_price,
            **kwargs
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def create_complete_inventory_snapshot(
        db: Session,
        snapshot_date: date,
        company_id: uuid.UUID,
        center_id: uuid.UUID,
        items_data: List[dict] = None,
        **kwargs
    ):
        """완전한 재고 스냅샷을 생성합니다."""
        if items_data is None:
            items_data = [
                {"product_name": "쌀", "quantity": 50, "quality": "A", "unit_price": 10000.0},
                {"product_name": "보리", "quantity": 30, "quality": "B", "unit_price": 8000.0},
            ]
        
        # 스냅샷 생성
        total_quantity = sum(item["quantity"] for item in items_data)
        total_price = sum(item["quantity"] * item["unit_price"] for item in items_data)
        
        snapshot = InventorySnapshotFactory.create_center_inventory_snapshot(
            db, snapshot_date, company_id, center_id, total_quantity, total_price, **kwargs
        )
        
        # 아이템들 생성
        items = []
        for item_data in items_data:
            item = InventorySnapshotFactory.create_center_inventory_snapshot_item(
                db, snapshot.id, **item_data
            )
            items.append(item)
        
        return {"snapshot": snapshot, "items": items}


class ContractFactory:
    @staticmethod
    def create_contract(
        db: Session,
        supplier_company_id: uuid.UUID,
        receiver_company_id: uuid.UUID,
        title: str = "테스트 계약",
        total_amount: float = 1000000.0,
        status: str = "pending",
        contract_date: datetime = None,
        creator_id: uuid.UUID = None,
        **kwargs
    ):
        """계약을 생성합니다."""
        from app.transactions.contract.models import Contract
        from app.transactions.common.models import ContractStatus
        
        if contract_date is None:
            contract_date = datetime.now()
        
        # Enum 값 변환
        contract_status = ContractStatus(status) if isinstance(status, str) else status
        
        contract = Contract(
            supplier_company_id=supplier_company_id,
            receiver_company_id=receiver_company_id,
            title=title,
            total_price=total_amount,
            contract_status=contract_status,
            contract_datetime=contract_date,
            creator_id=creator_id,
            **kwargs
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def create_contract_item(
        db: Session,
        contract_id: uuid.UUID,
        product_name: str = "쌀",
        quantity: int = 100,
        quality: str = "A",
        unit_price: float = 10000.0,
        **kwargs
    ):
        """계약 아이템을 생성합니다."""
        from app.transactions.contract.models import ContractItem
        from app.transactions.common.models import ProductQuality
        
        # Enum 값 변환
        product_quality = ProductQuality(quality) if isinstance(quality, str) else quality
        
        item = ContractItem(
            contract_id=contract_id,
            product_name=product_name,
            quantity=quantity,
            quality=product_quality,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            **kwargs
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def create_complete_contract(
        db: Session,
        supplier_company_id: uuid.UUID,
        receiver_company_id: uuid.UUID,
        creator_id: uuid.UUID = None,
        items_data: List[dict] = None,
        **kwargs
    ):
        """완전한 계약을 생성합니다."""
        if items_data is None:
            items_data = [
                {"product_name": "쌀", "quantity": 100, "quality": "A", "unit_price": 10000.0},
                {"product_name": "보리", "quantity": 50, "quality": "B", "unit_price": 8000.0},
            ]
        
        total_amount = sum(item["quantity"] * item["unit_price"] for item in items_data)
        
        contract = ContractFactory.create_contract(
            db, supplier_company_id, receiver_company_id, 
            total_amount=total_amount, creator_id=creator_id, **kwargs
        )
        
        items = []
        for item_data in items_data:
            item = ContractFactory.create_contract_item(db, contract.id, **item_data)
            items.append(item)
        
        return {"contract": contract, "items": items}


class ShipmentFactory:
    @staticmethod
    def create_shipment(
        db: Session,
        contract_id: uuid.UUID,
        creator_id: uuid.UUID,
        title: str = "테스트 출하",
        supplier_company_id: uuid.UUID = None,
        receiver_company_id: uuid.UUID = None,
        shipment_datetime: datetime = None,
        status: str = "pending",
        **kwargs
    ):
        """출하를 생성합니다."""
        from app.transactions.shipment.models import Shipment
        from app.transactions.common.models import ShipmentStatus
        
        if shipment_datetime is None:
            shipment_datetime = datetime.now()
        
        # Enum 값 변환
        shipment_status = ShipmentStatus(status) if isinstance(status, str) else status
        
        shipment = Shipment(
            contract_id=contract_id,
            creator_id=creator_id,
            title=title,
            supplier_company_id=supplier_company_id,
            receiver_company_id=receiver_company_id,
            shipment_datetime=shipment_datetime,
            shipment_status=shipment_status,
            **kwargs
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        return shipment

    @staticmethod
    def create_shipment_item(
        db: Session,
        shipment_id: uuid.UUID,
        product_name: str = "쌀",
        quantity: int = 50,
        quality: str = "A",
        unit_price: float = 10000.0,
        **kwargs
    ):
        """출하 아이템을 생성합니다."""
        from app.transactions.shipment.models import ShipmentItem
        from app.transactions.common.models import ProductQuality
        
        # Enum 값 변환
        product_quality = ProductQuality(quality) if isinstance(quality, str) else quality
        
        total_price = quantity * unit_price
        item = ShipmentItem(
            shipment_id=shipment_id,
            product_name=product_name,
            quantity=quantity,
            quality=product_quality,
            unit_price=unit_price,
            total_price=total_price,
            **kwargs
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def create_complete_shipment(
        db: Session,
        contract_id: uuid.UUID,
        creator_id: uuid.UUID,
        items_data: List[dict] = None,
        **kwargs
    ):
        """완전한 출하를 생성합니다."""
        if items_data is None:
            items_data = [
                {"product_name": "쌀", "quantity": 50, "quality": "A", "unit_price": 10000.0},
                {"product_name": "보리", "quantity": 30, "quality": "B", "unit_price": 8000.0},
            ]
        
        shipment = ShipmentFactory.create_shipment(
            db, contract_id, creator_id, **kwargs
        )
        
        items = []
        for item_data in items_data:
            item = ShipmentFactory.create_shipment_item(db, shipment.id, **item_data)
            items.append(item)
        
        return {"shipment": shipment, "items": items}

