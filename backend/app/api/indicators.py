"""指标查询 API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import FinancialMetric, Department
from ..schemas import IndicatorOut, IndicatorListResponse

router = APIRouter(prefix="/api/indicators", tags=["indicators"])

# 允许查询的字段白名单
ALLOWED_METRICS = {
    "revenue", "cost", "operating_expense",
    "net_profit", "cash_flow", "accounts_receivable",
}


@router.get("", response_model=IndicatorListResponse)
def list_indicators(
    department_id: Optional[int] = Query(None, description="部门 ID"),
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    metrics: Optional[str] = Query(None, description="逗号分隔的字段列表，如 revenue,cost"),
    db: Session = Depends(get_db),
):
    """查询月度经营指标，支持多条件筛选"""
    query = db.query(
        FinancialMetric,
        Department.name.label("department_name"),
    ).join(Department, FinancialMetric.department_id == Department.id)

    if department_id is not None:
        query = query.filter(FinancialMetric.department_id == department_id)
    if year is not None:
        query = query.filter(FinancialMetric.year == year)
    if month is not None:
        query = query.filter(FinancialMetric.month == month)

    query = query.order_by(
        FinancialMetric.department_id,
        FinancialMetric.year,
        FinancialMetric.month,
    )

    rows = query.all()
    result: list[IndicatorOut] = []
    for metric, dept_name in rows:
        result.append(IndicatorOut(
            id=metric.id,
            department_id=metric.department_id,
            department_name=dept_name,
            year=metric.year,
            month=metric.month,
            revenue=metric.revenue,
            cost=metric.cost,
            operating_expense=metric.operating_expense,
            net_profit=metric.net_profit,
            cash_flow=metric.cash_flow,
            accounts_receivable=metric.accounts_receivable,
        ))

    return IndicatorListResponse(data=result, total=len(result))
