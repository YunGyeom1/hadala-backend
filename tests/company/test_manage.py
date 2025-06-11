from datetime import date, datetime, timedelta
from uuid import uuid4
from app.transactions.common.models import ProductQuality
from app.company.manage import crud, schemas
from app.company.common.models import Company
from app.transactions.retail_contract.models import RetailContract, RetailContractItem

def test_get_retail_contract_daily_summary(db):
    # 테스트 데이터 준비
    company1 = Company(
        id=uuid4(),
        name="딜리마트",
        business_number="123-45-67890"
    )
    company2 = Company(
        id=uuid4(),
        name="W4마트",
        business_number="234-56-78901"
    )
    receiver_company = Company(
        id=uuid4(),
        name="수신회사",
        business_number="345-67-89012"
    )
    
    db.add_all([company1, company2, receiver_company])
    db.commit()

    # 계약 1 생성
    contract1 = RetailContract(
        id=uuid4(),
        title="테스트 계약 1",
        supplier_company_id=company1.id,
        receiver_company_id=receiver_company.id,
        delivery_datetime=datetime(2025, 1, 3, 10, 0),
        total_price=1000
    )
    db.add(contract1)
    db.flush()

    # 계약 1의 아이템들
    items1 = [
        RetailContractItem(
            contract_id=contract1.id,
            product_name="청경채",
            quality=ProductQuality.A,
            quantity=100,
            unit_price=5,
            total_price=500
        ),
        RetailContractItem(
            contract_id=contract1.id,
            product_name="당근",
            quality=ProductQuality.A,
            quantity=200,
            unit_price=2.5,
            total_price=500
        )
    ]
    db.add_all(items1)

    # 계약 2 생성
    contract2 = RetailContract(
        id=uuid4(),
        title="테스트 계약 2",
        supplier_company_id=company2.id,
        receiver_company_id=receiver_company.id,
        delivery_datetime=datetime(2025, 1, 3, 14, 0),
        total_price=500
    )
    db.add(contract2)
    db.flush()

    # 계약 2의 아이템들
    items2 = [
        RetailContractItem(
            contract_id=contract2.id,
            product_name="청경채",
            quality=ProductQuality.B,
            quantity=50,
            unit_price=5,
            total_price=250
        ),
        RetailContractItem(
            contract_id=contract2.id,
            product_name="당근",
            quality=ProductQuality.B,
            quantity=60,
            unit_price=4.17,
            total_price=250
        )
    ]
    db.add_all(items2)
    db.commit()

    # 테스트 실행
    start_date = date(2025, 1, 1)
    end_date = date(2025, 1, 5)
    result = crud.get_retail_contract_daily_summary(
        db=db,
        company_id=receiver_company.id,
        start_date=start_date,
        end_date=end_date
    )

    # 결과 검증
    assert "2025-01-03" in result.summaries
    daily_summary = result.summaries["2025-01-03"]
    
    # 딜리마트 검증
    assert "딜리마트" in daily_summary
    assert "청경채" in daily_summary["딜리마트"]
    assert "당근" in daily_summary["딜리마트"]
    assert daily_summary["딜리마트"]["청경채"]["A"] == 100
    assert daily_summary["딜리마트"]["당근"]["A"] == 200

    # W4마트 검증
    assert "W4마트" in daily_summary
    assert "청경채" in daily_summary["W4마트"]
    assert "당근" in daily_summary["W4마트"]
    assert daily_summary["W4마트"]["청경채"]["B"] == 50
    assert daily_summary["W4마트"]["당근"]["B"] == 60 