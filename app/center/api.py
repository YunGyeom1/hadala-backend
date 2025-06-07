from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database.session import get_db
from app.center import crud, schemas
from app.core.auth.dependencies import verify_access_token
from app.core.auth.schemas import VerifyTokenRequest
from app.company.crud import get_company

router = APIRouter(prefix="/centers", tags=["centers"])

@router.post("", response_model=schemas.CenterResponse)
def create_center(
    center: schemas.CenterCreate,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    새로운 수집 센터를 생성합니다.
    회사 소유자만 가능합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 회사 소유자 확인
    company = get_company(db, center.company_id)
    if not company or company.owner != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="수집 센터를 생성할 권한이 없습니다"
        )
    
    return crud.create_center(db, center)

@router.get("", response_model=List[schemas.CenterResponse])
def get_centers(
    skip: int = 0,
    limit: int = 100,
    filters: schemas.CenterFilter = None,
    token: VerifyTokenRequest = None,
    db: Session = Depends(get_db)
):
    """
    수집 센터 목록을 조회합니다.
    필터링, 페이지네이션, 제한을 지원합니다.
    """
    # 토큰이 제공된 경우 사용자 ID 추출
    user_id = None
    if token:
        token_data = verify_access_token(token.access_token)
        user_id = UUID(token_data.sub)
    
    return crud.get_centers(db, skip, limit, filters)

@router.get("/{center_id}", response_model=schemas.CenterResponse)
def get_center(
    center_id: UUID,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    특정 수집 센터의 정보를 조회합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    center = crud.get_center(db, center_id)
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="수집 센터를 찾을 수 없습니다"
        )
    
    return center

@router.put("/{center_id}", response_model=schemas.CenterResponse)
def update_center(
    center_id: UUID,
    center_update: schemas.CenterUpdate,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    수집 센터 정보를 수정합니다.
    회사 소유자만 가능합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 수집 센터 조회
    center = crud.get_center(db, center_id)
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="수집 센터를 찾을 수 없습니다"
        )
    
    # 회사 소유자 확인
    company = get_company(db, center.company_id)
    if not company or company.owner != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="수집 센터를 수정할 권한이 없습니다"
        )
    
    return crud.update_center(db, center_id, center_update)

@router.delete("/{center_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_center(
    center_id: UUID,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    수집 센터를 삭제합니다.
    회사 소유자만 가능합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 수집 센터 조회
    center = crud.get_center(db, center_id)
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="수집 센터를 찾을 수 없습니다"
        )
    
    # 회사 소유자 확인
    company = get_company(db, center.company_id)
    if not company or company.owner != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="수집 센터를 삭제할 권한이 없습니다"
        )
    
    if not crud.delete_center(db, center_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수집 센터 삭제 중 오류가 발생했습니다"
        )

@router.get("/{center_id}/wholesalers", response_model=List[schemas.WholesalerInCenter])
def get_center_wholesalers(
    center_id: UUID,
    skip: int = 0,
    limit: int = 100,
    token: VerifyTokenRequest = None,
    db: Session = Depends(get_db)
):
    """
    수집 센터에 등록된 도매상 목록을 조회합니다.
    """
    # 토큰이 제공된 경우 사용자 ID 추출
    user_id = None
    if token:
        token_data = verify_access_token(token.access_token)
        user_id = UUID(token_data.sub)
    
    center = crud.get_center(db, center_id)
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="수집 센터를 찾을 수 없습니다"
        )
    
    return crud.get_center_wholesalers(db, center_id, skip, limit) 