from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.company.detail.wholesale.models import WholesaleCompanyDetail
from . import schemas
from datetime import date, timedelta

from app.company.inventory_snapshot.crud import get_center_inventory_snapshots_by_date
from app.company.inventory_snapshot.schemas import CenterInventorySnapshotResponse
from app.company.inventory_snapshot.crud import generate_center_inventory_snapshot
from app.company.center.models import Center

def create_wholesale_company_detail(
    db: Session,
    company_id: UUID,
    detail: schemas.WholesaleCompanyDetailCreate
) -> WholesaleCompanyDetail:
    """
    도매회사 상세 정보를 생성합니다.
    """
    db_detail = WholesaleCompanyDetail(
        company_id=company_id,
        **detail.model_dump()
    )
    db.add(db_detail)
    db.commit()
    db.refresh(db_detail)
    return db_detail

def get_wholesale_company_detail(
    db: Session,
    company_id: UUID
) -> Optional[WholesaleCompanyDetail]:
    """
    도매회사 상세 정보를 조회합니다.
    """
    return db.query(WholesaleCompanyDetail).filter(
        WholesaleCompanyDetail.company_id == company_id
    ).first()

def update_wholesale_company_detail(
    db: Session,
    company_id: UUID,
    detail_update: schemas.WholesaleCompanyDetailUpdate
) -> Optional[WholesaleCompanyDetail]:
    """
    도매회사 상세 정보를 업데이트합니다.
    """
    db_detail = get_wholesale_company_detail(db, company_id)
    if not db_detail:
        return None

    update_data = detail_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_detail, field, value)
    
    db.commit()
    db.refresh(db_detail)
    return db_detail

def get_company_inventory_snapshot(
    db: Session,
    company_id: UUID,
    snapshot_date: date
) -> Optional[schemas.CompanyInventorySnapshot]:
    """
    특정 날짜의 회사 전체 재고 스냅샷을 조회합니다.
    """
    # 해당 날짜의 모든 집하장 스냅샷 조회
    center_snapshots = get_center_inventory_snapshots_by_date(
        db=db,
        company_id=company_id,
        snapshot_date=snapshot_date
    )
    
    if not center_snapshots:
        return None
    
    return schemas.CompanyInventorySnapshot(
        snapshot_date=snapshot_date,
        center_snapshots=center_snapshots
    )

def search_company_inventory_snapshots(
    db: Session,
    company_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 10,
    auto_generate: bool = True
) -> tuple[List[schemas.CompanyInventorySnapshot], int]:
    """
    회사의 재고 스냅샷을 검색합니다.
    스냅샷이 없는 날짜의 경우 자동으로 생성합니다.
    """
    # 날짜 범위 내의 모든 집하장 스냅샷 조회
    center_snapshots = get_center_inventory_snapshots_by_date(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    
    # 날짜별로 스냅샷 그룹화
    snapshots_by_date: dict[date, List[CenterInventorySnapshotResponse]] = {}
    for snapshot in center_snapshots:
        if snapshot.snapshot_date not in snapshots_by_date:
            snapshots_by_date[snapshot.snapshot_date] = []
        snapshots_by_date[snapshot.snapshot_date].append(snapshot)
    
    # 자동 생성이 활성화된 경우, 없는 날짜의 스냅샷 생성
    if auto_generate:
        # 회사의 모든 집하장 조회
        centers = db.query(Center).filter(
            Center.company_id == company_id
        ).all()
        
        # 날짜 범위 내의 모든 날짜에 대해
        current_date = start_date or date.today()
        end_date = end_date or date.today()
        
        while current_date <= end_date:
            if current_date not in snapshots_by_date:
                # 각 집하장에 대해 스냅샷 생성
                for center in centers:
                    snapshot = generate_center_inventory_snapshot(
                        db=db,
                        company_id=company_id,
                        center_id=center.id,
                        snapshot_date=current_date
                    )
                    if snapshot:
                        if current_date not in snapshots_by_date:
                            snapshots_by_date[current_date] = []
                        snapshots_by_date[current_date].append(snapshot)
            
            current_date += timedelta(days=1)
    
    # 회사 전체 스냅샷 생성
    company_snapshots = [
        schemas.CompanyInventorySnapshot(
            snapshot_date=date,
            center_snapshots=snapshots
        )
        for date, snapshots in snapshots_by_date.items()
    ]
    
    # 전체 개수 조회
    total = len(snapshots_by_date)
    
    return company_snapshots, total
