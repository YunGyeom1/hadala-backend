from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from app.profile.models import Profile, ProfileType, ProfileRole
from app.profile.schemas import MyProfileCreate, MyProfileUpdate, ExternalProfileCreate, ExternalProfileUpdate

def create_my_profile(db: Session, profile: MyProfileCreate, user_id: UUID) -> Profile:
    """
    새로운 프로필을 생성합니다.
    """
    profile_data = profile.model_dump()
    profile_data["user_id"] = user_id
    db_profile = Profile(**profile_data)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def create_external_profile(db: Session, profile: ExternalProfileCreate) -> Profile:
    """
    user_id가 없는 공개 프로필을 생성합니다.
    """
    profile_data = profile.model_dump()
    profile_data["user_id"] = None
    db_profile = Profile(**profile_data)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def get_profile(db: Session, profile_id: UUID) -> Optional[Profile]:
    """
    ID로 프로필을 조회합니다.
    """
    return db.query(Profile).filter(Profile.id == profile_id).first()

def get_profile_by_username(db: Session, username: str) -> Optional[Profile]:
    """
    username으로 프로필을 조회합니다.
    """
    return db.query(Profile).filter(Profile.username == username).first()

def search_profiles(db: Session, username: str, profile_type: ProfileType, skip: int = 0, limit: int = 10) -> List[Profile]:
    """
    username의 일부와 일치하는 프로필들을 검색합니다.
    """
    query = db.query(Profile).options(joinedload(Profile.company))
    if username:
        query = query.filter(Profile.username.ilike(f"%{username}%"))
    if profile_type:
        query = query.filter(Profile.type == profile_type)
    return query.offset(skip).limit(limit).all()

def get_my_profiles_by_user_id(db: Session, user_id: UUID) -> List[Profile]:
    """
    사용자 ID로 모든 프로필을 조회합니다.
    """
    return db.query(Profile).filter(Profile.user_id == user_id).all() 

def update_my_profile(db: Session, profile_id: UUID, profile_update: MyProfileUpdate) -> Profile :
    """
    프로필을 수정합니다.
    """
    db_profile = get_profile(db, profile_id)
    if not db_profile:
        return None
    
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_external_profile(db: Session, profile_id: UUID, profile_update: ExternalProfileUpdate) -> Profile:
    """
    공개 프로필을 수정합니다.
    """
    db_profile = get_profile(db, profile_id)
    if not db_profile:
        return None

    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_profile_role(db: Session, profile_id: UUID, new_role: ProfileRole) -> Profile:    
    profile = get_profile(db, profile_id)
    if not profile:
        return None
    
    profile.role = new_role
    db.commit()
    db.refresh(profile)
    return profile