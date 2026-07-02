"""异常检测 API"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Anomaly, Department
from ..schemas import (
    AnomalyOut, AnomalyListResponse,
    AnomalyDetectRequest, AnomalyDetectResponse, AnomalyDetail,
)

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@router.get("", response_model=AnomalyListResponse)
def list_anomalies(
    department_id: Optional[int] = Query(None, description="部门 ID"),
    severity: Optional[str] = Query(None, description="严重程度: high/medium/low"),
    year: Optional[int] = Query(None, description="年份"),
    db: Session = Depends(get_db),
):
    """查询历史异常记录"""
    query = db.query(
        Anomaly, Department.name.label("department_name")
    ).join(Department, Anomaly.department_id == Department.id)

    if department_id is not None:
        query = query.filter(Anomaly.department_id == department_id)
    if severity is not None:
        query = query.filter(Anomaly.severity == severity)
    if year is not None:
        query = query.filter(Anomaly.year == year)

    query = query.order_by(Anomaly.severity.desc(), Anomaly.year, Anomaly.month)

    rows = query.all()
    data: list[AnomalyOut] = []
    summary: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for anomaly, dept_name in rows:
        data.append(AnomalyOut(
            id=anomaly.id,
            department_id=anomaly.department_id,
            department_name=dept_name,
            year=anomaly.year,
            month=anomaly.month,
            metric_name=anomaly.metric_name,
            metric_label=anomaly.metric_label,
            actual_value=anomaly.actual_value,
            expected_range=anomaly.expected_range,
            deviation_pct=anomaly.deviation_pct,
            severity=anomaly.severity,
            description=anomaly.description,
            detected_at=anomaly.detected_at,
        ))
        sev = anomaly.severity
        if sev in summary:
            summary[sev] += 1

    return AnomalyListResponse(data=data, total=len(data), summary=summary)


@router.post("/detect", response_model=AnomalyDetectResponse)
def detect_anomalies_endpoint(req: AnomalyDetectRequest, db: Session = Depends(get_db)):
    """触发异常检测：用 Isolation Forest 检测指定年月的数据，结果写入数据库"""
    from ..services.anomaly_detector import detect_anomalies
    from ..models import Department

    anomalies_data = detect_anomalies(db, req.year, req.month, req.contamination)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # 先删除同一年月的旧检测结果（避免重复累积）
    db.query(Anomaly).filter(
        Anomaly.year == req.year,
        Anomaly.month == req.month,
    ).delete(synchronize_session="fetch")

    # 写入 anomalies 表
    saved_count = 0
    for a in anomalies_data:
        # 查找 department_id
        dept = db.query(Department).filter(Department.name == a["department_name"]).first()
        if dept is None:
            continue
        record = Anomaly(
            department_id=dept.id,
            year=req.year,
            month=req.month,
            metric_name=a["metric_name"],
            metric_label=a["metric_label"],
            actual_value=a["actual_value"],
            expected_range=a["expected_range"],
            deviation_pct=a["deviation_pct"],
            severity=a["severity"],
            description=a.get("description", ""),
            detected_at=now_iso,
        )
        db.add(record)
        saved_count += 1

    db.commit()

    details = [
        AnomalyDetail(
            department_name=a["department_name"],
            metric_name=a["metric_name"],
            metric_label=a["metric_label"],
            actual_value=a["actual_value"],
            expected_range=a["expected_range"],
            deviation_pct=a["deviation_pct"],
            severity=a["severity"],
            description=a.get("description", ""),
        )
        for a in anomalies_data
    ]

    return AnomalyDetectResponse(anomalies_found=saved_count, details=details)
