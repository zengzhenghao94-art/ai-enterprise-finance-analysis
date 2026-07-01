"""异常检测服务 —— Isolation Forest + 降级规则"""

import numpy as np


def _isolation_forest_detect(metrics_data: list[dict], contamination: float) -> list[dict]:
    """用 Isolation Forest 检测异常，返回异常详情列表"""
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    n_samples = len(metrics_data)
    if n_samples < 6:
        return []

    # 构建特征矩阵
    features = []
    for m in metrics_data:
        revenue = m["revenue"]
        cost = m["cost"]
        net_profit = m["net_profit"]
        gross_margin = (revenue - cost) / revenue * 100 if revenue > 0 else 0
        profit_margin = net_profit / revenue * 100 if revenue > 0 else 0
        cost_ratio = cost / revenue if revenue > 0 else 0
        features.append([
            revenue, cost, m["operating_expense"], net_profit,
            m["cash_flow"], m["accounts_receivable"],
            gross_margin, profit_margin, cost_ratio,
        ])

    X = np.array(features, dtype=np.float64)
    X_scaled = StandardScaler().fit_transform(X)

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
    )
    labels = model.fit_predict(X_scaled)  # 1 = normal, -1 = anomaly

    anomaly_indices = np.where(labels == -1)[0]
    normal_indices = np.where(labels == 1)[0]

    if len(anomaly_indices) == 0:
        return []

    # P0-2: 小样本下 IF 可能把所有点判为异常，此时 normal_X 为空，后续计算产生 NaN
    if len(normal_indices) == 0:
        return []

    normal_X = X[normal_indices]
    metric_names = [
        ("revenue", "营业收入"), ("cost", "营业成本"),
        ("operating_expense", "运营费用"), ("net_profit", "净利润"),
        ("cash_flow", "现金流"), ("accounts_receivable", "应收账款"),
        ("gross_margin", "毛利率"), ("profit_margin", "净利率"),
        ("cost_ratio", "成本收入比"),
    ]

    anomalies = []
    for idx in anomaly_indices:
        row = metrics_data[idx]
        for col_idx, (m_name, m_label) in enumerate(metric_names):
            actual = X[idx, col_idx]
            normal_vals = normal_X[:, col_idx]
            mean_val = float(np.mean(normal_vals))
            std_val = float(np.std(normal_vals))
            if std_val < 1e-9:
                continue

            z_score = (actual - mean_val) / std_val
            if abs(z_score) < 1.5:
                continue

            deviation_pct = round((float(actual) - mean_val) / mean_val * 100, 1) if mean_val != 0 else 0.0
            abs_dev = abs(deviation_pct)

            if abs_dev > 30:
                severity = "high"
            elif abs_dev > 15:
                severity = "medium"
            else:
                severity = "low"

            expected_low = round(mean_val - 2 * std_val, 2)
            expected_high = round(mean_val + 2 * std_val, 2)

            anomalies.append({
                "department_name": row.get("department_name", f"部门{row['department_id']}"),
                "year": row["year"],
                "month": row["month"],
                "metric_name": m_name,
                "metric_label": m_label,
                "actual_value": round(float(actual), 2),
                "expected_range": f"{expected_low:.1f}-{expected_high:.1f}",
                "deviation_pct": deviation_pct,
                "severity": severity,
                "description": "",
            })

    return anomalies


def _rule_based_detect(metrics_data: list[dict]) -> list[dict]:
    """降级方案：简单规则检测 —— 环比超过 30% 标为异常"""
    anomalies = []
    n = len(metrics_data)
    if n < 2:
        return []

    latest = metrics_data[-1]
    prev = metrics_data[-2]

    metric_names = [
        ("revenue", "营业收入"), ("cost", "营业成本"),
        ("operating_expense", "运营费用"), ("net_profit", "净利润"),
        ("cash_flow", "现金流"), ("accounts_receivable", "应收账款"),
    ]

    def calc_derived(m):
        rev = m["revenue"]
        gm = (rev - m["cost"]) / rev * 100 if rev > 0 else 0
        pm = m["net_profit"] / rev * 100 if rev > 0 else 0
        cr = m["cost"] / rev if rev > 0 else 0
        return gm, pm, cr

    latest_derived = calc_derived(latest)
    prev_derived = calc_derived(prev)
    derived_names = [
        ("gross_margin", "毛利率"), ("profit_margin", "净利率"), ("cost_ratio", "成本收入比")
    ]

    all_metrics = (
        [(metric_names[i][0], metric_names[i][1], latest[metric_names[i][0]], prev[metric_names[i][0]])
         for i in range(len(metric_names))]
        + [(derived_names[i][0], derived_names[i][1], latest_derived[i], prev_derived[i])
           for i in range(len(derived_names))]
    )

    for m_name, m_label, curr_val, prev_val in all_metrics:
        if prev_val == 0:
            continue
        deviation_pct = round((curr_val - prev_val) / abs(prev_val) * 100, 1)
        abs_dev = abs(deviation_pct)
        if abs_dev < 30:
            continue

        severity = "high" if abs_dev > 50 else ("medium" if abs_dev > 40 else "low")
        anomalies.append({
            "department_name": latest.get("department_name", f"部门{latest['department_id']}"),
            "year": latest["year"],
            "month": latest["month"],
            "metric_name": m_name,
            "metric_label": m_label,
            "actual_value": round(curr_val, 2),
            "expected_range": f"{prev_val:.1f} (上月值)",
            "deviation_pct": deviation_pct,
            "severity": severity,
            "description": "",
        })

    return anomalies


def detect_anomalies(db_session, year: int, month: int, contamination: float = 0.1) -> list[dict]:
    """检测指定年月的异常指标

    Args:
        db_session: SQLAlchemy session
        year: 目标年份
        month: 目标月份
        contamination: Isolation Forest 污染率参数

    Returns:
        AnomalyDetail 字典列表（仅目标月）
    """
    from ..models import FinancialMetric, Department

    # 查询最近 12 个月的数据（含目标月）
    metrics = (
        db_session.query(FinancialMetric)
        .filter(
            ((FinancialMetric.year == year) & (FinancialMetric.month <= month))
            | ((FinancialMetric.year == year - 1) & (FinancialMetric.month > month))
        )
        .order_by(FinancialMetric.department_id, FinancialMetric.year, FinancialMetric.month)
        .all()
    )

    if not metrics:
        return []

    # 按部门分组
    dept_rows: dict[int, list] = {}
    dept_names: dict[int, str] = {}
    for m in metrics:
        dept_rows.setdefault(m.department_id, []).append(m)
        if m.department_id not in dept_names:
            dept = db_session.query(Department).filter(Department.id == m.department_id).first()
            dept_names[m.department_id] = dept.name if dept else f"部门{m.department_id}"

    all_anomalies = []

    for dept_id, rows in dept_rows.items():
        data = []
        for r in rows:
            data.append({
                "department_id": r.department_id,
                "department_name": dept_names.get(dept_id, ""),
                "year": r.year,
                "month": r.month,
                "revenue": r.revenue,
                "cost": r.cost,
                "operating_expense": r.operating_expense,
                "net_profit": r.net_profit,
                "cash_flow": r.cash_flow,
                "accounts_receivable": r.accounts_receivable,
            })

        try:
            raw = _isolation_forest_detect(data, contamination)
        except Exception as e:
            print(f"[anomaly_detector] Isolation Forest 失败，降级为规则检测: {repr(e)}")
            raw = _rule_based_detect(data)

        # 只保留目标年月的异常
        for a in raw:
            if a["year"] == year and a["month"] == month:
                all_anomalies.append(a)

    # 去重：同一部门同一指标只保留一条
    seen = set()
    unique = []
    for a in all_anomalies:
        key = (a["department_name"], a["metric_name"])
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique
