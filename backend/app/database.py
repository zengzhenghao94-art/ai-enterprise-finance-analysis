"""数据库连接配置 —— SQLAlchemy 2.0 sessionmaker"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite 数据库文件路径
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "finance.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """FastAPI 依赖注入：每次请求获取独立 session，结束时自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表（如果尚未存在）"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
