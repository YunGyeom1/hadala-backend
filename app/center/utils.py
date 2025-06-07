from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.center.models import Center
from app.wholesaler.utils import get_wholesaler
from app.user.models import User
from app.company.utils import check_company_permission


def get_center(db: Session, center_id: UUID) -> Center:
    center = db.query(Center).filter(Center.id == center_id).first()
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection center not found"
        )
    return center


def check_center_permission(
    db: Session,
    user: User,
    center_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    allowed_roles: Optional[List[str]] = None
) -> Center:
    """
    센터 존재 여부와 도매상의 권한을 검증하고,
    문제가 없으면 센터 객체를 반환합니다.
    - center_id가 주어지면 해당 센터 조회 후 권한 검증
    - center_id가 없고 company_id만 주어지면 센터는 None으로 반환되지만 권한은 검증
    """
    center = None

    if center_id:
        center = get_center(db, center_id)
        company_id = center.company_id

    if allowed_roles:
        wholesaler = get_wholesaler(db, user.id)
        if (
            not wholesaler or
            wholesaler.company_id != company_id or
            wholesaler.role not in allowed_roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 작업을 수행할 권한이 없습니다"
            )

    return center or Center(company_id=company_id)


def check_center_permission_by_user(db: Session, center_id: UUID, user_id: UUID) -> Center:
    center = get_center(db, center_id)
    check_company_permission(db, center.company_id, user_id)
    return center