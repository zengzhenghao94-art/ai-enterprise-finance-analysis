"""pytest 配置 —— 共享 fixture：TestClient + 内存数据库"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 指向项目根目录，确保 .env 和 prompts/ 正确加载
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 加载 .env（测试前必须）
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from app.database import get_db
from app.models import Base
from app.main import app
from app.services.data_generator import generate_and_seed


@pytest.fixture(scope="session")
def engine():
    """会话级内存 SQLite 引擎（URI 模式 + cache=shared 共享同一内存库）"""
    return create_engine(
        "sqlite:///file::memory:?cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )


@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def db_session(engine, TestingSessionLocal):
    """每次测试前重建表结构 + 种子数据，测试后回滚"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # 生成种子数据
    try:
        generate_and_seed(session)
    except Exception:
        session.rollback()
        raise
    session.commit()

    # 用 FastAPI 内置的 dependency_overrides 替换 get_db
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    # 清理
    session.rollback()
    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
