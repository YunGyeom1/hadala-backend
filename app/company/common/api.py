from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.profile.schemas import ProfileResponse
from app.profile.dependencies import get_current_profile
from app.database.session import get_db
from app.profile.models import Profile
from . import schemas, crud
from app.company.center.crud import create_center, remove_center
from app.company.center.schemas import CenterCreate, CenterResponse

router = APIRouter(prefix="/companies", tags=["companies"])

@router.post("/create", response_model=schemas.CompanyResponse)
def create_company(
    company: schemas.CompanyCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    새로운 회사를 생성합니다.
    """
    if crud.get_company_by_name(db, company.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 회사명입니다"
        )
    return crud.create_company(db, company, current_profile.id)

@router.get("/search", response_model=List[schemas.CompanyResponse])
def search_companies(
    name: str = Query(None, description="검색할 회사명"),
    company_type: str = Query(None, description="회사 타입"),
    skip: int = Query(0, ge=0, description="건너뛸 결과 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 결과 수"),
    db: Session = Depends(get_db)
):
    """
    회사를 검색합니다.
    """
    return crud.search_companies(db, name, company_type, skip, limit)

@router.get("/me", response_model=schemas.CompanyResponse)
def get_my_company(
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    내가 속한 회사를 조회합니다.
    """
    company_id = current_profile.company_id
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    return crud.get_company_by_id(db, company_id)

@router.get("/{company_id}", response_model=schemas.CompanyResponse)
def get_company(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    특정 회사를 조회합니다.
    """
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    return company

@router.put("/{company_id}", response_model=schemas.CompanyResponse)
def update_company(
    company_id: UUID,
    company_update: schemas.CompanyUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    회사 정보를 수정합니다.
    """
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    
    # 이름이 변경되었고, 다른 회사가 같은 이름을 사용하는 경우에만 에러
    if company_update.name and company_update.name != company.name:
        existing_company = crud.get_company_by_name(db, company_update.name)
        if existing_company and existing_company.id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 회사명입니다"
            )
    
    if company.owner_id != current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사에 대한 수정 권한이 없습니다"
        )
    
    return crud.update_company(db, company_id, company_update)

@router.put("/{company_id}/owner", response_model=schemas.CompanyResponse)
def update_company_owner(
    company_id: UUID,
    owner_update: schemas.CompanyOwnerUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    회사의 소유자를 변경합니다.
    """
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    if company.owner_id != current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사에 대한 소유권 변경 권한이 없습니다"
        )
    
    return crud.update_company_owner(db, company_id, owner_update.new_owner_id)

@router.post("/{company_id}/users", response_model=ProfileResponse)
def add_company_user(
    company_id: UUID,
    user_add: schemas.CompanyUserAdd,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    회사에 사용자를 추가합니다.
    """
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    if company.owner_id != current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사에 대한 사용자 추가 권한이 없습니다"
        )
    # 프로필 타입과 회사 타입이 일치하는지 확인
    profile = db.query(Profile).filter(Profile.id == user_add.profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다"
        )
    if profile.type.value != company.type.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회사 타입과 사용자 프로필 타입이 일치하지 않습니다"
        )

    return crud.add_company_user(db, company_id, user_add.profile_id, user_add.role)

@router.get("/{company_id}/users", response_model=List[ProfileResponse])
def get_company_users(
    company_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    회사에 속한 사용자 목록을 조회합니다.
    """
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    if company.owner_id != current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사에 대한 사용자 목록 조회 권한이 없습니다"
        )
    
    return crud.get_company_users(db, company_id)

@router.delete("/{company_id}/users/{user_id}", response_model=ProfileResponse)
def remove_company_user(
    company_id: UUID,
    user_id: UUID,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    회사에서 사용자를 제거합니다.
    """
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    if company.owner_id != current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사에 대한 사용자 제거 권한이 없습니다"
        )
    
    return crud.remove_company_user(db, company_id, user_id)

@router.post("/{company_id}/centers", response_model=CenterResponse)
def add_company_center(
    company_id: UUID,
    center_add: CenterCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    회사에 센터를 추가합니다.
    """
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    if company.owner_id != current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사에 대한 센터 추가 권한이 없습니다"
        )

    
    return create_center(db, company_id, center_add)
