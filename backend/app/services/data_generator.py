"""模拟财务数据生成 —— 带季节波动 + 噪声 + 异常注入"""

import numpy as np
from datetime import datetime, timezone


def generate_and_seed(db_session):
    """生成 3 个部门的 12 个月财务数据 + 3-5 条异常，写入数据库

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
        Department(name="财务部", manager="王经理"),
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
            "cf_noise": 0.20,
            "ar_base": 150, "ar_noise": 0.08,
        },
        "生产部": {
            "base_revenue": 800, "revenue_noise": 0.12,
            "cost_ratio": 0.72, "cost_noise": 0.06,
            "opex_ratio": 0.10, "opex_noise": 0.08,
            "profit_noise": 0.03,
            "cf_noise": 0.18,
            "ar_base": 200, "ar_noise": 0.07,
        },
        "财务部": {
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

    for dept in departments:
        p = dept_params[dept.name]
        for month in range(1, 13):
            season = monthly_season[month]
            ar_s = ar_season[month]

            revenue = p["base_revenue"] * season * (1 + np.random.uniform(-p["revenue_noise"], p["revenue_noise"]))
            cost = revenue * p["cost_ratio"] * (1 + np.random.uniform(-p["cost_noise"], p["cost_noise"]))
            opex = revenue * p["opex_ratio"] * (1 + np.random.uniform(-p["opex_noise"], p["opex_noise"]))
            net_profit = (revenue - cost - opex) * (1 + np.random.uniform(-p["profit_noise"], p["profit_noise"]))
            cash_flow = net_profit * (1 + np.random.uniform(-p["cf_noise"], p["cf_noise"]))
            ar = p["ar_base"] * ar_s * (1 + np.random.uniform(-p["ar_noise"], p["ar_noise"]))

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

    db_session.add_all(all_metrics)
    db_session.flush()

    # ---- 注入异常数据 ----
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    anomalies_data = [
        # 销售部 6 月：成本异常飙升（比正常高 50%）
        Anomaly(
            department_id=departments[0].id, year=2025, month=6,
            metric_name="cost_ratio", metric_label="成本收入比",
            actual_value=92.5, expected_range="55.0-80.0", deviation_pct=35.0,
            severity="high", description="6 月成本收入比异常偏高，原材料采购价大幅上涨导致成本失控",
            detected_at=now_iso,
        ),
        # 生产部 3 月：收入骤降
        Anomaly(
            department_id=departments[1].id, year=2025, month=3,
            metric_name="revenue", metric_label="营业收入",
            actual_value=520.0, expected_range="680.0-950.0", deviation_pct=-28.5,
            severity="medium", description="3 月收入显著低于预期，可能受春节后开工延迟影响",
            detected_at=now_iso,
        ),
        # 财务部 9 月：现金流异常
        Anomaly(
            department_id=departments[2].id, year=2025, month=9,
            metric_name="cash_flow", metric_label="现金流",
            actual_value=30.0, expected_range="50.0-90.0", deviation_pct=-45.0,
            severity="high", description="9 月现金流骤降，应收账款回收周期延长导致资金紧张",
            detected_at=now_iso,
        ),
        # 销售部 12 月：应收账款异常高
        Anomaly(
            department_id=departments[0].id, year=2025, month=12,
            metric_name="accounts_receivable", metric_label="应收账款",
            actual_value=280.0, expected_range="130.0-200.0", deviation_pct=55.0,
            severity="high", description="年末应收账款大幅高于正常水平，存在坏账风险",
            detected_at=now_iso,
        ),
        # 生产部 8 月：净利率偏低
        Anomaly(
            department_id=departments[1].id, year=2025, month=8,
            metric_name="profit_margin", metric_label="净利率",
            actual_value=8.2, expected_range="14.0-22.0", deviation_pct=-40.0,
            severity="high", description="8 月净利率异常偏低，运营费用超预算与毛利压缩叠加影响",
            detected_at=now_iso,
        ),
    ]
    db_session.add_all(anomalies_data)

    db_session.commit()
    print(f"[data_generator] 种子数据已生成：{len(departments)} 个部门，{len(all_metrics)} 条月度指标，{len(anomalies_data)} 条异常记录。")
