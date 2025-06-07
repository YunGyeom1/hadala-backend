from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.user.models import User
from app.wholesaler.models import Wholesaler
from typing import Optional, List

def get_current_user_company_id(current_user: User, db: Session) -> Optional[str]:
    """현재 사용자의 회사 ID를 반환합니다."""
    if current_user.wholesaler:
        return current_user.wholesaler.company_id
    return None

def verify_company_member(current_user: User, db: Session) -> None:
    """사용자가 회사 소속인지 확인합니다."""
    company_id = get_current_user_company_id(current_user, db)
    if not company_id:
        raise HTTPException(status_code=403, detail="회사 소속이 아닙니다.")

def verify_company_role(current_user: User, db: Session, allowed_roles: List[str]) -> None:
    """사용자의 회사 내 권한을 확인합니다."""
    verify_company_member(current_user, db)
    if not current_user.wholesaler or current_user.wholesaler.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

def get_company_member_dependency():
    """회사 소속 확인을 위한 의존성 함수를 반환합니다."""
    def _get_company_member(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> None:
        verify_company_member(current_user, db)
    return _get_company_member

def get_company_role_dependency(allowed_roles: List[str]):
    """회사 내 특정 권한 확인을 위한 의존성 함수를 반환합니다."""
    def _get_company_role(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> None:
        verify_company_role(current_user, db, allowed_roles)
    return _get_company_role 