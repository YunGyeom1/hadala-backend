import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.auth.models import User
from app.profile.models import Profile
from app.company.common.models import Company


class UserFactory:
    @staticmethod
    def create_user(
        db: Session,
        oauth_provider: str = "google",
        oauth_sub: str = None,
        picture_url: str = "https://example.com/picture.jpg"
    ) -> User:
        if oauth_sub is None:
            oauth_sub = str(uuid.uuid4())
        
        user = User(
            oauth_provider=oauth_provider,
            oauth_sub=oauth_sub,
            picture_url=picture_url
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


class ProfileFactory:
    @staticmethod
    def create_profile(
        db: Session,
        user_id: uuid.UUID = None,
        username: str = "testuser",
        name: str = "테스트 사용자",
        phone: str = "010-1234-5678",
        email: str = "test@example.com",
        role: str = "owner",
        type: str = "wholesaler"
    ) -> Profile:
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
            type=type
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

class CompanyFactory:
    @staticmethod
    def create_company(
        db: Session,
        name: str = "테스트 회사",
        type: str = "wholesaler",
        address: str = "서울시 강남구",
        phone: str = "02-1234-5678",
        email: str = "test@company.com",
        owner_id: uuid.UUID = None
    ) -> Company:
        if owner_id is None:
            profile = ProfileFactory.create_profile(db)
            owner_id = profile.user_id
        
        company = Company(
            name=name,
            type=type,
            address=address,
            phone=phone,
            email=email,
            owner_id=owner_id
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return company

