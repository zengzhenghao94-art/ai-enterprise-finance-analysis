"""经营简报生成 API"""

from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
import tempfile

from ..database import get_db
from ..models import FinancialMetric, Department, Anomaly
from ..schemas import ReportGenerateRequest, ReportGenerateResponse

router = APIRouter(prefix="/api/report", tags=["report"])


def _load_report_template() -> str:
    """加载简报生成的系统提示词模板"""
    template_path = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "report_template.txt"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


@router.post("/generate", response_model=ReportGenerateResponse)
def generate_report(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    """基于指定年月数据，生成 Markdown 格式经营简报"""
    from ..services.llm_client import query_llm, estimate_tokens

    # ---- 1. 查询指标数据 ----
    metric_query = db.query(
        FinancialMetric, Department.name.label("department_name")
    ).join(Department, FinancialMetric.department_id == Department.id).filter(
        FinancialMetric.year == req.year,
        FinancialMetric.month == req.month,
    )

    if req.department_id is not None:
        metric_query = metric_query.filter(FinancialMetric.department_id == req.department_id)

    metric_rows = metric_query.all()
    if not metric_rows:
        raise HTTPException(
            status_code=404,
            detail=f"未找到 {req.year} 年 {req.month} 月的数据",
        )

    # ---- 2. 查询异常数据 ----
    anomaly_rows: list = []
    if req.include_anomalies:
        anomaly_query = db.query(
            Anomaly, Department.name.label("department_name")
        ).join(Department, Anomaly.department_id == Department.id).filter(
            Anomaly.year == req.year,
            Anomaly.month == req.month,
        )
        if req.department_id is not None:
            anomaly_query = anomaly_query.filter(Anomaly.department_id == req.department_id)
        anomaly_rows = anomaly_query.all()

    # ---- 3. 组装数据文本 ----
    # 提取部门列表
    dept_names_in_data = sorted(set(dept_name for _, dept_name in metric_rows))
    is_multi_dept = len(dept_names_in_data) > 1

    data_text = f"## {req.year} 年 {req.month} 月经营数据\n\n"
    data_text += f"共 {len(dept_names_in_data)} 个部门：{'、'.join(dept_names_in_data)}\n\n"

    for metric, dept_name in metric_rows:
        data_text += (
            f"### {dept_name}\n"
            f"- 营业收入: {metric.revenue} 万元\n"
            f"- 营业成本: {metric.cost} 万元（成本收入比: {metric.cost / metric.revenue * 100:.1f}%）\n"
            f"- 运营费用: {metric.operating_expense} 万元\n"
            f"- 净利润: {metric.net_profit} 万元（净利率: {metric.net_profit / metric.revenue * 100:.1f}%）\n"
            f"- 经营现金流: {metric.cash_flow} 万元\n"
            f"- 应收账款: {metric.accounts_receivable} 万元\n"
            f"- 毛利率: {(metric.revenue - metric.cost) / metric.revenue * 100:.1f}%\n\n"
        )

    if anomaly_rows:
        data_text += "## 当月异常记录\n\n"
        for anom, dept_name in anomaly_rows:
            data_text += (
                f"- [{anom.severity.upper()}] {dept_name} - {anom.metric_label}: "
                f"实际 {anom.actual_value}, 预期 {anom.expected_range}, "
                f"偏离 {anom.deviation_pct:+.1f}%\n"
            )
        data_text += "\n"
    else:
        data_text += "（当月无异常记录）\n\n"

    # ---- 4. 加载系统提示词模板 + 调用 LLM ----
    system_prompt = _load_report_template()

    # 根据是否多部门调整分析要求
    if is_multi_dept:
        dept_analysis_req = (
            "2. **每个部门单独分析**：逐一列出各部门的收入、成本、利润和关键比率，"
            "明确标注部门名称，进行部门间横向对比（如毛利率排名、收入占比等）\n"
        )
    else:
        dept_analysis_req = "2. 分析该部门的收入、成本、利润和关键比率\n"

    report_prompt = (
        f"{data_text}\n\n"
        "请根据以上数据生成一份经营分析简报。要求：\n"
        "1. 用 Markdown 格式输出，先给出总体评价\n"
        + dept_analysis_req +
        "3. 针对异常指标给出风险提示\n"
        "4. 在文章末尾，用 `### KEY_FINDINGS` 标记关键发现（每条一行，用 - 列表）\n"
    )

    try:
        report_content = query_llm(report_prompt, system_prompt=system_prompt if system_prompt else None)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # ---- 5. 提取 key_findings ----
    key_findings: list[str] = []
    if "### KEY_FINDINGS" in report_content:
        parts = report_content.split("### KEY_FINDINGS")
        findings_section = parts[-1].strip()
        for line in findings_section.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                key_findings.append(line[2:])
            elif line.startswith("* "):
                key_findings.append(line[2:])
    elif "key_findings" in report_content.lower():
        # fallback: 尝试找 JSON 风格的标记
        key_findings = ["（解析失败，请查看完整报告）"]
    else:
        key_findings = ["（未检测到 KEY_FINDINGS 标记，请查看完整报告）"]

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    if req.department_id and metric_rows:
        dept_suffix = f" - {metric_rows[0][1]}"
    elif is_multi_dept:
        dept_suffix = " - 全公司"
    else:
        dept_suffix = ""

    return ReportGenerateResponse(
        title=f"{req.year}年{req.month}月经营分析简报{dept_suffix}",
        generated_at=now_iso,
        content=report_content,
        key_findings=key_findings,
    )


@router.post("/export")
def export_report(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    """生成简报并导出为 ZIP（HTML + 图表 PNG + CSS），浏览器触发下载。"""
    from ..services.report import (
        render_trend_chart,
        render_kpi_comparison,
        render_anomaly_chart,
        render_dept_radar,
        build_report_html,
        package_zip,
    )

    # ---- 1. 复刻 generate_report 的数据查询 ----
    metric_query = db.query(
        FinancialMetric, Department.name.label("department_name")
    ).join(Department, FinancialMetric.department_id == Department.id).filter(
        FinancialMetric.year == req.year,
        FinancialMetric.month == req.month,
    )
    if req.department_id is not None:
        metric_query = metric_query.filter(FinancialMetric.department_id == req.department_id)
    metric_rows = metric_query.all()
    if not metric_rows:
        raise HTTPException(status_code=404, detail=f"未找到 {req.year} 年 {req.month} 月的数据")

    anomaly_rows: list = []
    if req.include_anomalies:
        anomaly_query = db.query(Anomaly, Department.name.label("department_name")
        ).join(Department, Anomaly.department_id == Department.id).filter(
            Anomaly.year == req.year, Anomaly.month == req.month,
        )
        if req.department_id is not None:
            anomaly_query = anomaly_query.filter(Anomaly.department_id == req.department_id)
        anomaly_rows = anomaly_query.all()

    dept_names_in_data = sorted(set(dept_name for _, dept_name in metric_rows))
    is_multi_dept = len(dept_names_in_data) > 1

    # ---- 2. 组装数据文本 + 调 LLM 生成报告 ----
    data_text = f"## {req.year} 年 {req.month} 月经营数据\n\n"
    data_text += f"共 {len(dept_names_in_data)} 个部门：{'、'.join(dept_names_in_data)}\n\n"
    for metric, dept_name in metric_rows:
        data_text += (
            f"### {dept_name}\n"
            f"- 营业收入: {metric.revenue} 万元\n"
            f"- 营业成本: {metric.cost} 万元（成本收入比: {metric.cost / metric.revenue * 100:.1f}%）\n"
            f"- 运营费用: {metric.operating_expense} 万元\n"
            f"- 净利润: {metric.net_profit} 万元（净利率: {metric.net_profit / metric.revenue * 100:.1f}%）\n"
            f"- 经营现金流: {metric.cash_flow} 万元\n"
            f"- 应收账款: {metric.accounts_receivable} 万元\n"
            f"- 毛利率: {(metric.revenue - metric.cost) / metric.revenue * 100:.1f}%\n\n"
        )
    if anomaly_rows:
        data_text += "## 当月异常记录\n\n"
        for anom, dn in anomaly_rows:
            data_text += f"- [{anom.severity.upper()}] {dn} - {anom.metric_label}: 实际 {anom.actual_value}, 偏离 {anom.deviation_pct:+.1f}%\n"
        data_text += "\n"

    from ..services.llm_client import query_llm
    system_prompt = _load_report_template()
    if is_multi_dept:
        dept_analysis_req = (
            "2. **每个部门单独分析**：逐一列出各部门的收入、成本、利润和关键比率，"
            "明确标注部门名称，进行部门间横向对比\n"
        )
    else:
        dept_analysis_req = "2. 分析该部门的收入、成本、利润和关键比率\n"

    report_prompt = (
        f"{data_text}\n\n请根据以上数据生成一份经营分析简报。要求：\n"
        "1. 用 Markdown 格式输出，先给出总体评价\n"
        + dept_analysis_req +
        "3. 针对异常指标给出风险提示\n"
        "4. 在文章末尾，用 `### KEY_FINDINGS` 标记关键发现（每条一行，用 - 列表）\n"
    )
    try:
        report_content = query_llm(report_prompt, system_prompt=system_prompt if system_prompt else None)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # ---- 3. 拉全年指标数据用于图表（趋势图需要 12 个月） ----
    trend_query = db.query(FinancialMetric).filter(FinancialMetric.year == req.year)
    if req.department_id is not None:
        trend_query = trend_query.filter(FinancialMetric.department_id == req.department_id)
    trend_metrics = trend_query.order_by(FinancialMetric.month).all()

    # 全公司趋势：按月聚合
    from collections import defaultdict
    monthly_agg = defaultdict(lambda: {"revenue": 0.0, "cost": 0.0, "net_profit": 0.0})
    for tm in trend_metrics:
        m = tm.month
        monthly_agg[m]["revenue"] += tm.revenue
        monthly_agg[m]["cost"] += tm.cost
        monthly_agg[m]["net_profit"] += tm.net_profit
    trend_data = [
        {"month": m, "revenue": v["revenue"], "cost": v["cost"], "net_profit": v["net_profit"]}
        for m, v in sorted(monthly_agg.items())
    ]

    # ---- 4. 渲染图表 ----
    export_root = Path(tempfile.mkdtemp(prefix="report_export_"))
    chart_dir = export_root / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)

    trend_path = render_trend_chart(trend_data, req.year, chart_dir)
    anomaly_path = render_anomaly_chart(
        [
            {
                "metric_label": a.metric_label,
                "dept_name": dn,
                "deviation_pct": a.deviation_pct,
                "severity": a.severity,
            }
            for a, dn in anomaly_rows
        ],
        chart_dir,
    )

    # KPI 对比：从 metric_rows 提取
    kpi_data = []
    for metric, dept_name in metric_rows:
        kpi_data.append({
            "dept_name": dept_name,
            "revenue": metric.revenue,
            "cost": metric.cost,
            "net_profit": metric.net_profit,
        })
    kpi_path = render_kpi_comparison(kpi_data, chart_dir) if len(kpi_data) >= 2 else None

    # 雷达图：需要派生指标
    radar_data = []
    for metric, dept_name in metric_rows:
        rev = metric.revenue
        radar_data.append({
            "dept_name": dept_name,
            "毛利率": round((rev - metric.cost) / rev * 100, 1) if rev else 0,
            "净利率": round(metric.net_profit / rev * 100, 1) if rev else 0,
            "现金流比率": round(metric.cash_flow / rev * 100, 1) if rev else 0,
            "费用率": round(100 - metric.operating_expense / rev * 100, 1) if rev else 0,
            "收入规模": round(rev / 100, 1),
        })
    radar_path = render_dept_radar(radar_data, chart_dir) if len(radar_data) >= 3 else None

    # ---- 5. 构建 HTML ----
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    if req.department_id and metric_rows:
        dept_label = metric_rows[0][1]
    elif is_multi_dept:
        dept_label = "全公司"
    else:
        dept_label = ""

    chart_refs = {
        "trend": "charts/trend.png",
        "kpi": "charts/kpi_comparison.png" if kpi_path else "",
        "anomaly": "charts/anomaly.png",
        "radar": "charts/dept_radar.png" if radar_path else "",
    }

    anomaly_meta = []
    for a, dn in anomaly_rows:
        anomaly_meta.append({
            "dept_name": dn,
            "metric_label": a.metric_label,
            "actual_value": a.actual_value,
            "expected_range": a.expected_range,
            "deviation_pct": a.deviation_pct,
            "severity": a.severity,
        })

    metadata = {
        "title": f"{req.year}年{req.month}月经营分析简报",
        "year": req.year,
        "month": req.month,
        "dept": dept_label,
        "generated_at": now_iso,
        "anomalies": anomaly_meta,
    }

    html_path = build_report_html(report_content, chart_refs, metadata, export_root)

    # ---- 6. ZIP 打包 ----
    zip_path = package_zip(html_path, chart_dir, export_root, "经营分析简报.zip")

    # 返回文件（文件名用 ASCII + RFC 5987 编码中文）
    safe_name = f"{req.year}-{req.month:02d}-report.zip"
    cn_name = f"{req.year}年{req.month}月经营分析简报.zip"
    encoded_name = quote(cn_name.encode('utf-8'))
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=safe_name,
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{encoded_name}",
        },
    )
