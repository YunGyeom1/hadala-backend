from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.session import get_db
from app.wholesaler import crud, schemas
from app.core.auth.utils import verify_access_token
from app.core.auth.schemas import VerifyTokenRequest
from app.company.crud import get_company

router = APIRouter(prefix="/wholesalers", tags=["wholesalers"])

@router.get("/me", response_model=schemas.WholesalerResponse)
def get_my_info(
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 도매상의 정보를 조회합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 도매상 정보 조회
    wholesaler = crud.get_wholesaler_by_user_id(db, user_id)
    if not wholesaler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도매상 정보를 찾을 수 없습니다"
        )
    
    return wholesaler

@router.put("/me", response_model=schemas.WholesalerResponse)
def update_my_info(
    wholesaler_update: schemas.WholesalerUpdate,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 도매상의 정보를 수정합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 도매상 정보 조회
    wholesaler = crud.get_wholesaler_by_user_id(db, user_id)
    if not wholesaler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도매상 정보를 찾을 수 없습니다"
        )
    
    return crud.update_wholesaler(db=db, wholesaler_id=wholesaler.id, wholesaler_update=wholesaler_update)

@router.get("/{wholesaler_id}", response_model=schemas.WholesalerResponse)
def get_wholesaler(
    wholesaler_id: UUID,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    특정 도매상의 정보를 조회합니다.
    같은 회사 소속 도매상만 조회 가능합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 요청자의 도매상 정보 조회
    requester = crud.get_wholesaler_by_user_id(db, user_id)
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 조회할 수 있습니다"
        )
    
    # 대상 도매상 정보 조회
    target = crud.get_wholesaler(db, wholesaler_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도매상을 찾을 수 없습니다"
        )
    
    # 같은 회사 소속인지 확인
    if requester.company_id != target.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="같은 회사 소속 도매상만 조회할 수 있습니다"
        )
    
    return target

@router.post("/company/{company_id}", response_model=schemas.WholesalerResponse)
def add_wholesaler_to_company(
    company_id: UUID,
    wholesaler: schemas.WholesalerCreate,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    회사에 도매상을 추가합니다.
    오너나 매니저만 가능합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 요청자의 도매상 정보 조회
    requester = crud.get_wholesaler_by_user_id(db, user_id)
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 추가할 수 있습니다"
        )
    
    # 회사 정보 조회
    company = get_company(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    
    # 권한 확인
    if requester.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사의 도매상만 추가할 수 있습니다"
        )
    
    if requester.role not in ["owner", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="오너나 매니저만 도매상을 추가할 수 있습니다"
        )
    
    # 이미 회사에 소속된 도매상인지 확인
    existing_wholesaler = crud.get_wholesaler_by_user_id(db, wholesaler.user_id)
    if existing_wholesaler and existing_wholesaler.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 다른 회사에 소속된 도매상입니다"
        )
    
    return crud.create_wholesaler(db=db, wholesaler=wholesaler)

@router.put("/{wholesaler_id}/role", response_model=schemas.WholesalerResponse)
def update_wholesaler_role(
    wholesaler_id: UUID,
    role_update: schemas.WholesalerRoleUpdate,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    도매상의 역할을 변경합니다.
    오너나 매니저만 가능합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 요청자의 도매상 정보 조회
    requester = crud.get_wholesaler_by_user_id(db, user_id)
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 역할을 변경할 수 있습니다"
        )
    
    # 대상 도매상 정보 조회
    target = crud.get_wholesaler(db, wholesaler_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도매상을 찾을 수 없습니다"
        )
    
    # 같은 회사 소속인지 확인
    if requester.company_id != target.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="같은 회사 소속 도매상만 역할을 변경할 수 있습니다"
        )
    
    # 권한 확인
    if requester.role not in ["owner", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="오너나 매니저만 역할을 변경할 수 있습니다"
        )
    
    # 오너로 변경하려면 오너 권한 필요
    if role_update.role == "owner" and requester.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="오너로 변경하려면 오너 권한이 필요합니다"
        )
    
    return crud.update_wholesaler_role(db=db, wholesaler_id=wholesaler_id, role_update=role_update)

@router.delete("/{wholesaler_id}/company", response_model=schemas.WholesalerResponse)
def remove_wholesaler_from_company(
    wholesaler_id: UUID,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    도매상을 회사에서 제거합니다.
    오너나 매니저만 가능합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 요청자의 도매상 정보 조회
    requester = crud.get_wholesaler_by_user_id(db, user_id)
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 제거할 수 있습니다"
        )
    
    # 대상 도매상 정보 조회
    target = crud.get_wholesaler(db, wholesaler_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도매상을 찾을 수 없습니다"
        )
    
    # 같은 회사 소속인지 확인
    if requester.company_id != target.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="같은 회사 소속 도매상만 제거할 수 있습니다"
        )
    
    # 권한 확인
    if requester.role not in ["owner", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="오너나 매니저만 도매상을 제거할 수 있습니다"
        )
    
    # 오너는 제거할 수 없음
    if target.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="오너는 제거할 수 없습니다"
        )
    
    return crud.remove_wholesaler_from_company(db=db, wholesaler_id=wholesaler_id)