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
    """触发异常检测：Isolation Forest + Z-score 交叉验证 → LLM 解释 → 写入数据库"""
    from ..services.anomaly_detector import detect_anomalies
    from ..services.llm_client import query_llm
    from ..models import Department

    anomalies_data = detect_anomalies(db, req.year, req.month, req.contamination)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # 先删除同一年月的旧检测结果（避免重复累积）
    db.query(Anomaly).filter(
        Anomaly.year == req.year,
        Anomaly.month == req.month,
    ).delete(synchronize_session="fetch")

    # ---- LLM 交叉验证：为每条异常生成自然语言解释 ----
    if anomalies_data:
        # 构建批量解释 prompt
        lines = []
        for i, a in enumerate(anomalies_data):
            lines.append(
                f"{i+1}. {a['department_name']} - {a['metric_label']}: "
                f"实际 {a['actual_value']}, 预期 {a['expected_range']}, "
                f"偏差 {a['deviation_pct']:+.1f}%, 严重程度 {a['severity']}"
            )
        explain_prompt = (
            "以下是通过 Isolation Forest（无监督异常检测）和 Z-score（特征偏离分析）"
            "交叉验证发现的经营数据异常。请用 1-2 句话解释每条异常的可能原因和业务影响：\n\n"
            + "\n".join(lines) +
            "\n\n对每条异常，用以下格式回复（每条一行）：\n"
            "编号. 解释内容"
        )
        try:
            explanations_text = query_llm(explain_prompt)
            # 解析 LLM 返回的解释，按编号映射
            explanation_map = {}
            for line in explanations_text.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() and "." in line[:3]):
                    parts = line.split(". ", 1)
                    if len(parts) == 2:
                        try:
                            idx = int(parts[0]) - 1
                            explanation_map[idx] = parts[1]
                        except ValueError:
                            continue
            # 回填解释
            for i, a in enumerate(anomalies_data):
                a["description"] = explanation_map.get(i, "")
        except Exception as e:
            print(f"[anomalies] LLM 解释生成失败，使用数据自动描述: {repr(e)}")
            # 降级：基于数据生成描述
            for a in anomalies_data:
                if not a.get("description"):
                    a["description"] = (
                        f"{a['metric_label']}偏离正常范围{a['expected_range']}，"
                        f"偏差{a['deviation_pct']:+.1f}%。"
                        f"建议关注{a['department_name']}{req.year}年{req.month}月"
                        f"{a['metric_label']}异常变动。"
                    )

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
