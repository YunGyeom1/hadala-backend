from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database.session import get_db
from app.profile import crud, schemas
from app.core.auth.models import User
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile
from app.core.auth.dependencies import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

@router.post("/me", response_model=schemas.MyProfileResponse)
def create_profile(
    profile: schemas.MyProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    새로운 프로필을 생성합니다.
    """
    # username 중복 확인
    if crud.get_profile_by_username(db, profile.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 username입니다"
        )
    
    return crud.create_my_profile(db, profile, current_user.id)

@router.post("/public", response_model=schemas.ProfileResponse)
def create_public_profile(
    profile: schemas.ExternalProfileCreate,
    db: Session = Depends(get_db)
):
    """
    user_id가 없는 공개 프로필을 생성합니다.
    """
    if crud.get_profile_by_username(db, profile.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 username입니다"
        )
    return crud.create_dummy_profile(db, profile)

@router.get("/me", response_model=List[schemas.MyProfileResponse])
def get_my_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    로그인한 사용자의 모든 프로필을 조회합니다.
    """
    return crud.get_my_profiles_by_user_id(db, current_user.id)

@router.get("/search", response_model=List[schemas.ProfileResponse])
def search_profiles(
    username: str = Query(None, min_length=1, description="검색할 username"),
    profile_type: schemas.ProfileType = Query(None, description="프로필 타입"),
    skip: int = Query(0, ge=0, description="건너뛸 결과 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 결과 수"),
    db: Session = Depends(get_db)
):
    """
    username과 profile_type을 조합하여 프로필을 검색합니다.
    """
    return crud.search_profiles(db, username, profile_type, skip, limit)

@router.get("/{profile_id}", response_model=schemas.ProfileResponse)
def get_profile(
    profile_id: UUID,
    db: Session = Depends(get_db)
):
    """
    특정 프로필을 조회합니다.
    """
    profile = crud.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다"
        )
    return profile 

@router.put("/{profile_id}", response_model=schemas.MyProfileResponse)
def update_my_profile(
    profile_id: UUID,
    profile_update: schemas.MyProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 프로필을 수정합니다.
    """
    profile = crud.get_profile(db, profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다"
        )
    if profile.user_id is not None and profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 프로필에 대한 접근 권한이 없습니다"
        )

    return crud.update_my_profile(db, profile_id, profile_update)

@router.put("/{profile_id}/role", response_model=schemas.ProfileResponse)
def update_profile_role(
    profile_id: UUID,
    new_role: schemas.ProfileRoleUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    profile = crud.get_profile(db, profile_id)
    if not profile or not profile.company_id:
        raise HTTPException(status_code=404, detail="프로필 또는 회사 정보가 없습니다")

    # user_id가 연결되지 않은 External Profile이거나, 현재 로그인한 사용자가 같은 회사의 owner인지 확인
    if profile.user_id:
        if profile.company_id != current_profile.company_id or current_profile.role != "owner":
            raise HTTPException(status_code=403, detail="권한이 없습니다")

    return crud.update_profile_role(db, profile.id, new_role.role) 