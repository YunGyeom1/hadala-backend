from sqlalchemy import create_engine, text
from app.database.base import Base
from app.core.config import settings

def create_tables():
    """데이터베이스 테이블을 새로 생성합니다."""
    engine = create_engine(settings.DATABASE_URL)
    
    # 기존 테이블 삭제 (CASCADE 사용)
    print("기존 테이블을 삭제합니다...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        conn.commit()
    
    # 새 테이블 생성
    print("새 테이블을 생성합니다...")
    Base.metadata.create_all(engine)
    
    print("데이터베이스 테이블 생성 완료!")

if __name__ == "__main__":
    create_tables() 