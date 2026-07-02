"""FastAPI 入口 —— 挂载路由、CORS、启动初始化"""

from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 加载 .env（必须在其他模块之前）
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, SessionLocal
from .schemas import HealthResponse
from .api.departments import router as dept_router
from .api.indicators import router as indicator_router
from .api.anomalies import router as anomaly_router
from .api.nl2sql import router as nl2sql_router
from .api.report import router as report_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库 + 生成种子数据"""
    init_db()
    from .services.data_generator import generate_and_seed
    db = SessionLocal()
    try:
        generate_and_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="企业财务分析 API", version="0.1.0", lifespan=lifespan)

# CORS — 开发阶段允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dept_router)
app.include_router(indicator_router)
app.include_router(anomaly_router)
app.include_router(nl2sql_router)
app.include_router(report_router)


@app.get("/api/health", response_model=HealthResponse)
def health():
    """健康检查"""
    return HealthResponse()
