from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.wholesale_company.company.models import Company
from app.users.user.models import User
from app.users.wholesaler.crud import get_wholesaler_by_user_id


def check_company_permission(
    db: Session,
    user: Optional[User] = None,
    company_id: UUID = None,
    allowed_roles: Optional[List[str]] = None
) -> Company:
    """
    회사 존재 여부와 사용자 권한을 확인하고, 실패 시 예외 발생
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    
    if allowed_roles:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다"
            )
        wholesaler = get_wholesaler_by_user_id(db, user.id)
        if wholesaler.company_id != company_id or wholesaler.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 작업을 수행할 권한이 없습니다"
            )

    return company