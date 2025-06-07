from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database.session import get_db
from app.company import crud, schemas
from app.core.auth.utils import verify_access_token
from app.core.auth.schemas import VerifyTokenRequest
from app.wholesaler.crud import get_wholesaler_by_user_id

router = APIRouter(prefix="/companies", tags=["companies"])

@router.post("/", response_model=schemas.CompanyResponse)
def create_company(
    company: schemas.CompanyCreate,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    새로운 회사를 생성합니다.
    로그인한 도매상이 오너로 지정됩니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 사용자의 도매상 정보 조회
    wholesaler = get_wholesaler_by_user_id(db, user_id)
    if not wholesaler:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 회사를 생성할 수 있습니다"
        )
    
    return crud.create_company(db=db, company=company, owner_id=wholesaler.id)

@router.get("/", response_model=List[schemas.CompanyResponse])
def get_companies(
    skip: int = 0,
    limit: int = 100,
    filters: schemas.CompanyFilter = None,
    db: Session = Depends(get_db)
):
    """
    필터링된 회사 목록을 조회합니다.
    """
    return crud.get_companies(db=db, skip=skip, limit=limit, filters=filters)

@router.get("/{company_id}", response_model=schemas.CompanyResponse)
def get_company(company_id: UUID, db: Session = Depends(get_db)):
    """
    ID로 회사를 조회합니다.
    """
    company = crud.get_company(db=db, company_id=company_id)
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
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    회사 정보를 업데이트합니다.
    오너만 수정할 수 있습니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 사용자의 도매상 정보 조회
    wholesaler = get_wholesaler_by_user_id(db, user_id)
    if not wholesaler:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 회사 정보를 수정할 수 있습니다"
        )
    
    # 회사 정보 조회
    company = crud.get_company(db=db, company_id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    
    # 오너 권한 확인
    if company.owner != wholesaler.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 오너만 정보를 수정할 수 있습니다"
        )
    
    return crud.update_company(db=db, company_id=company_id, company_update=company_update)

@router.get("/{company_id}/wholesalers", response_model=List[schemas.WholesalerInCompany])
def get_company_wholesalers(
    company_id: UUID,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    회사 소속 도매상 목록을 조회합니다.
    회사 소속 도매상만 조회할 수 있습니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 사용자의 도매상 정보 조회
    wholesaler = get_wholesaler_by_user_id(db, user_id)
    if not wholesaler:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 조회할 수 있습니다"
        )
    
    # 회사 정보 조회
    company = crud.get_company(db=db, company_id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    
    # 회사 소속 확인
    if wholesaler.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 소속 도매상만 조회할 수 있습니다"
        )
    
    return crud.get_company_wholesalers(db=db, company_id=company_id)

@router.get("/{company_id}/collection-centers", response_model=List[schemas.CollectionCenterInCompany])
def get_company_collection_centers(
    company_id: UUID,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    회사 소유 집하장 목록을 조회합니다.
    회사 소속 도매상만 조회할 수 있습니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 사용자의 도매상 정보 조회
    wholesaler = get_wholesaler_by_user_id(db, user_id)
    if not wholesaler:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 조회할 수 있습니다"
        )
    
    # 회사 정보 조회
    company = crud.get_company(db=db, company_id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    
    # 회사 소속 확인
    if wholesaler.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 소속 도매상만 조회할 수 있습니다"
        )
    
    return crud.get_company_collection_centers(db=db, company_id=company_id)