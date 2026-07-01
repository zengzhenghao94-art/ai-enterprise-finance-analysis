"""模拟财务数据生成 —— 带季节波动 + 噪声 + 增长趋势 + 异常注入"""

import numpy as np
from datetime import datetime, timezone


def generate_and_seed(db_session):
    """生成 3 个部门的 12 个月财务数据 + 5 条异常，写入数据库

    只执行一次：如果数据库已有数据，跳过。
    """
    from ..models import Department, FinancialMetric, Anomaly

    # 检查是否已有数据
    existing = db_session.query(FinancialMetric).first()
    if existing is not None:
        print("[data_generator] 数据库已有数据，跳过种子生成。")
        return

    np.random.seed(42)

    # ---- 部门 ----
    departments = [
        Department(name="销售部", manager="张经理"),
        Department(name="生产部", manager="李经理"),
        Department(name="市场部", manager="王经理"),  # P0-a: 财务部→市场部（费用中心不产生营收）
    ]
    db_session.add_all(departments)
    db_session.flush()  # 获取 id

    # ---- 部门特性参数 ----
    dept_params = {
        "销售部": {
            "base_revenue": 500, "revenue_noise": 0.15,
            "cost_ratio": 0.68, "cost_noise": 0.05,
            "opex_ratio": 0.12, "opex_noise": 0.10,
            "profit_noise": 0.03,
            "cf_noise": 0.15,
            "ar_base": 150, "ar_noise": 0.08,
        },
        "生产部": {
            "base_revenue": 800, "revenue_noise": 0.12,
            "cost_ratio": 0.72, "cost_noise": 0.06,
            "opex_ratio": 0.10, "opex_noise": 0.08,
            "profit_noise": 0.03,
            "cf_noise": 0.15,
            "ar_base": 200, "ar_noise": 0.07,
        },
        "市场部": {  # P0-a: 原"财务部"
            "base_revenue": 300, "revenue_noise": 0.10,
            "cost_ratio": 0.60, "cost_noise": 0.04,
            "opex_ratio": 0.15, "opex_noise": 0.07,
            "profit_noise": 0.03,
            "cf_noise": 0.15,
            "ar_base": 80, "ar_noise": 0.06,
        },
    }

    # 月度季节系数（Q4 偏高）
    monthly_season = {
        1: 0.85, 2: 0.78, 3: 0.95, 4: 0.98, 5: 1.02, 6: 1.05,
        7: 1.00, 8: 1.03, 9: 1.08, 10: 1.12, 11: 1.18, 12: 1.25,
    }
    ar_season = {
        1: 0.90, 2: 0.85, 3: 0.90, 4: 0.92, 5: 0.95, 6: 0.98,
        7: 0.98, 8: 1.00, 9: 1.02, 10: 1.05, 11: 1.12, 12: 1.20,
    }

    all_metrics = []
    dept_month_map: dict[int, dict[int, object]] = {}  # dept_id → {month: FinancialMetric}

    for dept in departments:
        p = dept_params[dept.name]
        dept_month_map[dept.id] = {}
        for month in range(1, 13):
            season = monthly_season[month]
            ar_s = ar_season[month]

            # P1-4: 微弱线性增长趋势，避免全年水平线
            growth = 1 + month * 0.01

            revenue = p["base_revenue"] * season * growth * (1 + np.random.uniform(-p["revenue_noise"], p["revenue_noise"]))
            cost = revenue * p["cost_ratio"] * (1 + np.random.uniform(-p["cost_noise"], p["cost_noise"]))
            opex = revenue * p["opex_ratio"] * (1 + np.random.uniform(-p["opex_noise"], p["opex_noise"]))

            # P0-b: 净利润扣除 25% 企业所得税
            net_profit = (revenue - cost - opex) * 0.75 * (1 + np.random.uniform(-p["profit_noise"], p["profit_noise"]))

            ar = p["ar_base"] * ar_s * (1 + np.random.uniform(-p["ar_noise"], p["ar_noise"]))

            # P1-3: 现金流与应收账款耦合 —— AR 增加消耗现金流，AR 减少改善现金流
            if len(all_metrics) > 0 and all_metrics[-1].department_id == dept.id:
                ar_prev = all_metrics[-1].accounts_receivable
            else:
                ar_prev = ar  # 该部门首月，无上月数据，ΔAR=0
            cash_flow = net_profit * (1 + np.random.uniform(-p["cf_noise"], p["cf_noise"])) - (ar - ar_prev) * 0.3

            m = FinancialMetric(
                department_id=dept.id,
                year=2025,
                month=month,
                revenue=round(revenue, 2),
                cost=round(cost, 2),
                operating_expense=round(opex, 2),
                net_profit=round(net_profit, 2),
                cash_flow=round(cash_flow, 2),
                accounts_receivable=round(ar, 2),
            )
            all_metrics.append(m)
            dept_month_map[dept.id][month] = m

    db_session.add_all(all_metrics)
    db_session.flush()

    # ---- P0-c: 从实际数据计算异常值，再构造 Anomaly 记录 ----
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    def _metric_value(m, name: str) -> float:
        """从 FinancialMetric 对象提取原子或派生指标"""
        if name == "revenue":
            return m.revenue
        if name == "cost":
            return m.cost
        if name == "net_profit":
            return m.net_profit
        if name == "cash_flow":
            return m.cash_flow
        if name == "accounts_receivable":
            return m.accounts_receivable
        if name == "cost_ratio":
            return round(m.cost / m.revenue * 100, 1) if m.revenue > 0 else 0.0
        if name == "profit_margin":
            return round(m.net_profit / m.revenue * 100, 1) if m.revenue > 0 else 0.0
        return 0.0

    def _make_anomaly(dept_id: int, month: int, metric_name: str, metric_label: str, description: str):
        """基于实际数据构造一条 Anomaly 记录"""
        m = dept_month_map[dept_id][month]
        actual = _metric_value(m, metric_name)

        # 用该部门 12 个月的该指标计算正常范围（均值 ± 标准差）
        all_vals = [_metric_value(dept_month_map[dept_id][mo], metric_name) for mo in range(1, 13)]
        mean_val = float(np.mean(all_vals))
        std_val = float(np.std(all_vals))

        deviation_pct = round((actual - mean_val) / mean_val * 100, 1) if mean_val != 0 else 0.0
        abs_dev = abs(deviation_pct)

        if abs_dev > 30:
            severity = "high"
        elif abs_dev > 15:
            severity = "medium"
        else:
            severity = "low"

        expected_low = max(0, mean_val - std_val)
        expected_high = mean_val + std_val

        return Anomaly(
            department_id=dept_id, year=2025, month=month,
            metric_name=metric_name, metric_label=metric_label,
            actual_value=actual,
            expected_range=f"{expected_low:.1f}-{expected_high:.1f}",
            deviation_pct=deviation_pct, severity=severity,
            description=description, detected_at=now_iso,
        )

    anomalies_data = [
        _make_anomaly(1, 6, "cost_ratio", "成本收入比",
                      "6 月成本收入比异常偏高，原材料采购价大幅上涨导致成本失控"),
        _make_anomaly(2, 3, "revenue", "营业收入",
                      "3 月收入显著低于预期，可能受春节后开工延迟影响"),
        _make_anomaly(3, 9, "cash_flow", "现金流",
                      "9 月现金流骤降，应收账款回收周期延长导致资金紧张"),
        _make_anomaly(1, 12, "accounts_receivable", "应收账款",
                      "年末应收账款大幅高于正常水平，存在坏账风险"),
        _make_anomaly(2, 8, "profit_margin", "净利率",
                      "8 月净利率异常偏低，运营费用超预算与毛利压缩叠加影响"),
    ]
    db_session.add_all(anomalies_data)

    db_session.commit()
    print(f"[data_generator] 种子数据已生成：{len(departments)} 个部门，{len(all_metrics)} 条月度指标，{len(anomalies_data)} 条异常记录。")
