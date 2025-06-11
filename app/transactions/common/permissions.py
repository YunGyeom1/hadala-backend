from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.transactions.retail_contract import models as retail_models
from app.profile.models import Profile
from uuid import UUID

def check_contract_access(
    db: Session,
    contract_id: UUID,
    profile: Profile,
    require_ownership: bool = False
) -> retail_models.RetailContract:
    """
    계약에 대한 접근 권한을 검사합니다.
    
    Args:
        db: 데이터베이스 세션
        contract_id: 계약 ID
        profile: 현재 사용자 프로필
        require_ownership: True인 경우 계약의 당사자(공급자 또는 수령자)만 접근 가능
                        False인 경우 계약의 당사자 회사 소속이면 접근 가능
    
    Returns:
        RetailContract: 검증된 계약 객체
    
    Raises:
        HTTPException: 권한이 없는 경우
    """
    if not profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 소속이 아닙니다"
        )
    
    contract = db.query(retail_models.RetailContract).filter(
        retail_models.RetailContract.id == contract_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계약을 찾을 수 없습니다"
        )
    
    # 계약의 당사자 회사인지 확인
    is_contract_party = (
        contract.supplier_company_id == profile.company_id or
        contract.receiver_company_id == profile.company_id
    )
    
    if not is_contract_party:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="계약에 접근할 권한이 없습니다"
        )
    
    # 당사자 권한이 필요한 경우 추가 검사
    if require_ownership:
        is_owner = (
            (contract.supplier_company_id == profile.company_id and profile.is_supplier) or
            (contract.receiver_company_id == profile.company_id and profile.is_receiver)
        )
        
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="계약을 수정할 권한이 없습니다"
            )
    
    return contract 