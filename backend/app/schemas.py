"""Pydantic 接口定义 —— 前后端契约

每个接口的 Request / Response 模型。
这是前后端 Agent 并行开发的唯一合同——字段名改了这里必须同步改。
"""

from pydantic import BaseModel, Field
from typing import Optional


# ═══════════════════════════════════════════
# 部门
# ═══════════════════════════════════════════

class DepartmentOut(BaseModel):
    id: int
    name: str
    manager: str

    model_config = {"from_attributes": True}


class DepartmentListResponse(BaseModel):
    data: list[DepartmentOut]


# ═══════════════════════════════════════════
# 指标查询
# ═══════════════════════════════════════════

class IndicatorOut(BaseModel):
    """单条月度指标记录"""
    id: int
    department_id: int
    department_name: str           # JOIN 出来的，前端不用再查
    year: int
    month: int
    revenue: float
    cost: float
    operating_expense: float
    net_profit: float
    cash_flow: float
    accounts_receivable: float

    model_config = {"from_attributes": True}


class IndicatorListResponse(BaseModel):
    data: list[IndicatorOut]
    total: int


# ═══════════════════════════════════════════
# 异常检测
# ═══════════════════════════════════════════

class AnomalyDetail(BaseModel):
    department_name: str
    metric_name: str
    metric_label: str
    actual_value: float
    expected_range: str
    deviation_pct: float              # 负值=低于预期
    severity: str                     # high / medium / low
    description: str                  # LLM 生成的解释


class AnomalyDetectResponse(BaseModel):
    anomalies_found: int
    details: list[AnomalyDetail]


class AnomalyDetectRequest(BaseModel):
    """触发异常检测"""
    year: int = Field(..., ge=2020, le=2030, description="检测年份")
    month: int = Field(..., ge=1, le=12, description="检测截止月份")
    contamination: float = Field(0.1, ge=0.01, le=0.5, description="Isolation Forest 污染率参数")


class AnomalyOut(BaseModel):
    """异常记录（数据库查询用）"""
    id: int
    department_id: int
    department_name: str
    year: int
    month: int
    metric_name: str
    metric_label: str
    actual_value: float
    expected_range: str
    deviation_pct: float
    severity: str
    description: Optional[str] = None
    detected_at: str

    model_config = {"from_attributes": True}


class AnomalyListResponse(BaseModel):
    data: list[AnomalyOut]
    total: int
    summary: dict[str, int]           # {"high": 1, "medium": 2, "low": 0}


# ═══════════════════════════════════════════
# NL2SQL — 核心接口
# ═══════════════════════════════════════════

class NL2SQLRequest(BaseModel):
    """自然语言查询请求"""
    query: str = Field(..., min_length=1, max_length=500, description="用户自然语言输入")
    department_id: Optional[int] = Field(None, description="可选限定部门")


class NL2SQLResponse(BaseModel):
    query: str                        # 原始输入，原样返回
    sql_generated: str                # LLM 生成的 SQL
    result: list[dict]                # 查询结果（每行一个 dict）
    explanation: str                  # LLM 对结果的自然语言解释
    tokens_used: int                  # LLM token 消耗（用于答辩时展示成本）


# ═══════════════════════════════════════════
# 简报生成
# ═══════════════════════════════════════════

class ReportGenerateRequest(BaseModel):
    """简报生成请求"""
    department_id: Optional[int] = Field(None, description="None=全公司，指定则只分析该部门")
    year: int = Field(..., ge=2020, le=2030)
    month: int = Field(..., ge=1, le=12, description="报告截止月份")
    include_anomalies: bool = Field(True, description="是否包含异常分析章节")


class ReportGenerateResponse(BaseModel):
    title: str                        # 简报标题
    generated_at: str                 # 生成时间 ISO 格式
    content: str                      # Markdown 格式简报全文
    key_findings: list[str]           # 关键发现列表，方便前端独立展示


# ═══════════════════════════════════════════
# 通用
# ═══════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
