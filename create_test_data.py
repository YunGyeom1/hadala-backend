import uuid
from sqlalchemy.orm import sessionmaker
from app.database.session import engine
from app.profile.models import Profile, ProfileType, ProfileRole
from app.company.common.models import Company, CompanyType
from app.company.center.models import Center
from app.company.detail.wholesale.models import WholesaleCompanyDetail

def create_test_data():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 기존 테스트 데이터 삭제
        print("기존 테스트 데이터 삭제 중...")
        
        # 먼저 회사의 owner_id를 null로 설정
        test_companies = session.query(Company).filter(Company.name.like('test_%')).all()
        for company in test_companies:
            company.owner_id = None
        session.commit()
        
        # 그 다음 삭제
        session.query(Center).filter(Center.name.like('test_%')).delete()
        session.query(Center).filter(Center.name.like('%_center')).delete()
        session.query(Profile).filter(Profile.username.like('test_%')).delete()
        session.query(WholesaleCompanyDetail).filter(WholesaleCompanyDetail.company_id.in_(
            session.query(Company.id).filter(Company.name.like('test_%'))
        )).delete()
        session.query(Company).filter(Company.name.like('test_%')).delete()
        session.commit()
        print("기존 테스트 데이터 삭제 완료!")
        
        # 1. 테스트 회사들 생성 (중복 체크)
        def get_or_create_company(name, type_):
            company = session.query(Company).filter(Company.name == name).first()
            if company:
                print(f"기존 회사 사용: {name}")
                return company
            company = Company(
                id=uuid.uuid4(),
                name=name,
                type=type_
            )
            session.add(company)
            session.flush()
            print(f"신규 회사 생성: {name}")
            return company
        
        test_farmer_company = get_or_create_company('test_farmer_company', CompanyType.farmer)
        test_retailer_company = get_or_create_company('test_retailer_company', CompanyType.retailer)
        test_wholesaler_company = get_or_create_company('test_wholesaler_company', CompanyType.wholesaler)

        # 2. 도매상 상세 정보 생성 (중복 체크)
        def get_or_create_wholesale_detail(company, **kwargs):
            detail = session.query(WholesaleCompanyDetail).filter(WholesaleCompanyDetail.company_id == company.id).first()
            if detail:
                print(f"기존 도매상 상세정보 사용: {company.name}")
                return detail
            detail = WholesaleCompanyDetail(
                id=uuid.uuid4(),
                company_id=company.id,
                address=kwargs.get('address'),
                phone=kwargs.get('phone'),
                email=kwargs.get('email'),
                business_registration_number=kwargs.get('business_registration_number'),
                representative=kwargs.get('representative'),
                established_year=kwargs.get('established_year'),
                region=kwargs.get('region'),
            )
            session.add(detail)
            session.flush()
            print(f"신규 도매상 상세정보 생성: {company.name}")
            return detail
        get_or_create_wholesale_detail(
            test_wholesaler_company,
            address='서울시 마포구 테스트로 789',
            phone='02-3456-7890',
            email='wholesaler@test.com',
            business_registration_number='3456789012',
            representative='Test Wholesaler',
            established_year=2020,
            region='마포구',
        )

        # 3. 테스트 유저 생성 (중복 체크)
        def get_or_create_profile(username, name, type_, company, email, phone):
            profile = session.query(Profile).filter(Profile.username == username).first()
            if profile:
                print(f"기존 유저 사용: {username}")
                return profile
            profile = Profile(
                id=uuid.uuid4(),
                username=username,
                name=name,
                email=email,
                phone=phone,
                type=type_,
                role=ProfileRole.owner,
                company_id=company.id
            )
            session.add(profile)
            session.flush()
            print(f"신규 유저 생성: {username}")
            return profile
        test_user = get_or_create_profile('test_user', 'Test User', ProfileType.wholesaler, test_wholesaler_company, 'test@example.com', '01012345678')
        test_farmer = get_or_create_profile('test_farmer', 'Test Farmer', ProfileType.farmer, test_farmer_company, 'farmer@example.com', '01011111111')
        test_retailer = get_or_create_profile('test_retailer', 'Test Retailer', ProfileType.retailer, test_retailer_company, 'retailer@example.com', '01022222222')
        test_wholesaler = get_or_create_profile('test_wholesaler', 'Test Wholesaler', ProfileType.wholesaler, test_wholesaler_company, 'wholesaler@example.com', '01033333333')

        # 4. 센터 생성 (중복 체크)
        def get_or_create_center(name, company, address, region, latitude, longitude, phone, operating_start, operating_end):
            center = session.query(Center).filter(Center.name == name, Center.company_id == company.id).first()
            if center:
                print(f"기존 센터 사용: {name}")
                return center
            center = Center(
                id=uuid.uuid4(),
                name=name,
                company_id=company.id,
                address=address,
                region=region,
                latitude=latitude,
                longitude=longitude,
                phone=phone,
                operating_start=operating_start,
                operating_end=operating_end,
                is_operational=True
            )
            session.add(center)
            session.flush()
            print(f"신규 센터 생성: {name}")
            return center
        get_or_create_center('test_center1', test_wholesaler_company, '서울시 마포구 센터로 1', '마포구', 37.5665, 126.9780, '02-1111-1111', '09:00:00', '18:00:00')
        get_or_create_center('test_center2', test_wholesaler_company, '서울시 마포구 센터로 2', '마포구', 37.5666, 126.9781, '02-2222-2222', '08:00:00', '20:00:00')
        get_or_create_center('farmer_center', test_farmer_company, '경기도 수원시 농부로 1', '수원시', 37.2636, 127.0286, '031-1111-1111', '06:00:00', '16:00:00')
        get_or_create_center('retailer_center', test_retailer_company, '서울시 강남구 소매로 1', '강남구', 37.5172, 127.0473, '02-3333-3333', '10:00:00', '22:00:00')

        # 유저 생성 후 회사 owner_id 지정
        test_farmer_company.owner_id = test_farmer.id
        test_retailer_company.owner_id = test_retailer.id
        test_wholesaler_company.owner_id = test_wholesaler.id
        session.add(test_farmer_company)
        session.add(test_retailer_company)
        session.add(test_wholesaler_company)

        session.commit()
        print("테스트 데이터 생성/확인 완료!")
    except Exception as e:
        session.rollback()
        print(f"테스트 데이터 생성 실패: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_test_data() 