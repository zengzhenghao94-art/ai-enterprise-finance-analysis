"""集成测试 —— 覆盖全部 7 个 API 端点

运行方式：
  cd backend
  python -m pytest tests/ -v

注意：NL2SQL 和简报生成端点依赖 LLM API Key。如果 .env 未配置，
测试标记为 skip 而非 fail。
"""

import os
import pytest


# ═══════════════════════════════════════════
# 0. 健康检查
# ═══════════════════════════════════════════

def test_health(client):
    """GET /api/health 返回 ok"""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# ═══════════════════════════════════════════
# 1. 部门列表
# ═══════════════════════════════════════════

def test_departments(client):
    """GET /api/departments 返回 3 个部门"""
    res = client.get("/api/departments")
    assert res.status_code == 200
    data = res.json()
    assert len(data["data"]) == 3
    names = {d["name"] for d in data["data"]}
    assert names == {"销售部", "生产部", "市场部"}
    # 验证每个部门有 id, name, manager
    for d in data["data"]:
        assert "id" in d
        assert "name" in d
        assert "manager" in d


# ═══════════════════════════════════════════
# 2. 指标查询
# ═══════════════════════════════════════════

def test_indicators_all(client):
    """GET /api/indicators 返回 72 条记录（3部门 × 12月 × 2年）"""
    res = client.get("/api/indicators")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 72
    assert len(data["data"]) == 72


def test_indicators_filter_by_department(client):
    """GET /api/indicators?department_id=1 返回 24 条（12月 × 2年）"""
    res = client.get("/api/indicators?department_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 24
    for item in data["data"]:
        assert item["department_id"] == 1


def test_indicators_filter_by_month(client):
    """GET /api/indicators?month=6 返回 6 条（3部门 × 2年）"""
    res = client.get("/api/indicators?month=6")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 6


def test_indicators_response_structure(client):
    """验证指标响应包含完整字段（6 个原子指标 + 部门信息）"""
    res = client.get("/api/indicators?department_id=1&month=1")
    assert res.status_code == 200
    item = res.json()["data"][0]
    required_fields = [
        "id", "department_id", "department_name",
        "year", "month",
        "revenue", "cost", "operating_expense",
        "net_profit", "cash_flow", "accounts_receivable",
    ]
    for field in required_fields:
        assert field in item, f"缺少字段: {field}"
    # 验证数据类型
    assert isinstance(item["revenue"], (int, float))
    assert isinstance(item["year"], int)
    assert isinstance(item["month"], int)
    assert 1 <= item["month"] <= 12


# ═══════════════════════════════════════════
# 3. 异常查询
# ═══════════════════════════════════════════

def test_anomalies_list_has_seeds(client):
    """GET /api/anomalies 返回 5 条种子异常"""
    res = client.get("/api/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    assert len(data["data"]) == 5
    # 验证 summary
    assert "summary" in data
    for sev in ["high", "medium", "low"]:
        assert sev in data["summary"]


def test_anomalies_filter_by_severity(client):
    """GET /api/anomalies?severity=high 只返回 high"""
    res = client.get("/api/anomalies?severity=high")
    assert res.status_code == 200
    data = res.json()
    for item in data["data"]:
        assert item["severity"] == "high"


def test_anomalies_response_structure(client):
    """验证异常记录包含完整字段"""
    res = client.get("/api/anomalies")
    item = res.json()["data"][0]
    required_fields = [
        "id", "department_id", "department_name",
        "year", "month", "metric_name", "metric_label",
        "actual_value", "expected_range", "deviation_pct",
        "severity", "description", "detected_at",
    ]
    for field in required_fields:
        assert field in item, f"缺少字段: {field}"


# ═══════════════════════════════════════════
# 4. 异常检测触发
# ═══════════════════════════════════════════

def test_anomalies_detect_structure(client):
    """POST /api/anomalies/detect 返回结构正确"""
    res = client.post("/api/anomalies/detect", json={
        "year": 2025,
        "month": 6,
        "contamination": 0.15,
    })
    assert res.status_code == 200
    data = res.json()
    assert "anomalies_found" in data
    assert "details" in data
    assert isinstance(data["details"], list)


def test_anomalies_detect_invalid_year(client):
    """POST /api/anomalies/detect 年份超出范围返回 422"""
    res = client.post("/api/anomalies/detect", json={
        "year": 2019,
        "month": 6,
    })
    assert res.status_code == 422


def test_anomalies_detect_invalid_month(client):
    """POST /api/anomalies/detect 月份超出范围返回 422"""
    res = client.post("/api/anomalies/detect", json={
        "year": 2025,
        "month": 13,
    })
    assert res.status_code == 422


# ═══════════════════════════════════════════
# 5. NL2SQL 自然语言查询
# ═══════════════════════════════════════════

_llm_available = bool(
    os.getenv("LLM_API_KEY", "").strip()
    and os.getenv("LLM_API_KEY") != "your-api-key-here"
)

nl2sql_reason = "LLM_API_KEY 未配置，跳过 NL2SQL 实机测试"


@pytest.mark.skipif(not _llm_available, reason=nl2sql_reason)
def test_nl2sql_basic_query(client):
    """POST /api/query/nl2sql 基本查询：销售部全年收入"""
    res = client.post("/api/query/nl2sql", json={
        "query": "销售部2025年总收入是多少？",
        "department_id": None,
    })
    assert res.status_code == 200
    data = res.json()
    # 验证响应结构
    assert "query" in data
    assert "sql_generated" in data
    assert "result" in data
    assert "explanation" in data
    assert "tokens_used" in data
    # SQL 必须以 SELECT 开头
    assert data["sql_generated"].strip().upper().startswith("SELECT")
    # 至少有一条结果
    assert len(data["result"]) >= 1


@pytest.mark.skipif(not _llm_available, reason=nl2sql_reason)
def test_nl2sql_with_department_filter(client):
    """POST /api/query/nl2sql 限定部门：生产部 6 月数据"""
    res = client.post("/api/query/nl2sql", json={
        "query": "6月的收入、成本和净利润",
        "department_id": 2,
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["result"]) >= 1


def test_nl2sql_security_validate_sql_direct():
    """_validate_sql 纯函数：拦截非 SELECT 语句"""
    from app.api.nl2sql import _validate_sql

    # INSERT / UPDATE / DELETE 等应被拦截
    assert _validate_sql("SELECT * FROM financial_metrics") is True
    assert _validate_sql("INSERT INTO financial_metrics VALUES (1,2,3)") is False
    assert _validate_sql("UPDATE financial_metrics SET revenue=0") is False
    assert _validate_sql("DELETE FROM financial_metrics") is False
    assert _validate_sql("DROP TABLE financial_metrics") is False
    assert _validate_sql("SELECT 1; DROP TABLE financial_metrics") is False
    # strip() 后正常 SELECT 仍应通过
    assert _validate_sql("  SELECT * FROM financial_metrics") is True


def test_nl2sql_empty_query(client):
    """POST /api/query/nl2sql 空查询返回 422"""
    res = client.post("/api/query/nl2sql", json={
        "query": "",
    })
    assert res.status_code == 422


# ═══════════════════════════════════════════
# 6. 简报生成
# ═══════════════════════════════════════════

report_reason = "LLM_API_KEY 未配置，跳过简报生成实机测试"


@pytest.mark.skipif(not _llm_available, reason=report_reason)
def test_report_generate_full(client):
    """POST /api/report/generate 全公司简报"""
    res = client.post("/api/report/generate", json={
        "department_id": None,
        "year": 2025,
        "month": 6,
        "include_anomalies": True,
    })
    assert res.status_code == 200
    data = res.json()
    assert "title" in data
    assert "generated_at" in data
    assert "content" in data
    assert "key_findings" in data
    # 简报标题格式
    assert "2025" in data["title"] and "6" in data["title"]
    # 简报内容应为 Markdown 字符串
    assert isinstance(data["content"], str)
    assert len(data["content"]) > 100  # 至少 100 字符
    # key_findings 为列表
    assert isinstance(data["key_findings"], list)


@pytest.mark.skipif(not _llm_available, reason=report_reason)
def test_report_generate_department(client):
    """POST /api/report/generate 单部门简报"""
    res = client.post("/api/report/generate", json={
        "department_id": 1,
        "year": 2025,
        "month": 6,
        "include_anomalies": True,
    })
    assert res.status_code == 200
    data = res.json()
    # 单部门简报标题包含部门名
    assert "销售部" in data["title"]


def test_report_404_nonexistent_data(client):
    """POST /api/report/generate 不存在的年月返回 404"""
    res = client.post("/api/report/generate", json={
        "year": 2020,
        "month": 1,
    })
    assert res.status_code == 404


def test_report_invalid_year(client):
    """POST /api/report/generate 无效年份返回 422"""
    res = client.post("/api/report/generate", json={
        "year": 2019,
        "month": 6,
    })
    assert res.status_code == 422


# ═══════════════════════════════════════════
# 7. 数据真实性验证
# ═══════════════════════════════════════════

def test_data_not_all_same(client):
    """验证模拟数据不是等差数列——每月 revenue 有波动"""
    res = client.get("/api/indicators?department_id=1")
    revenues = [item["revenue"] for item in res.json()["data"]]
    # 12 个月不应该是同一个值
    assert len(set(revenues)) >= 10  # 至少 10 个不同值
    # 最大值/最小值比例应该有自然波动（季节系数×噪声）
    ratio = max(revenues) / min(revenues)
    assert 1.10 < ratio < 2.5  # Q4/Q1 正常波动范围


def test_seasonal_pattern(client):
    """验证模拟数据有季节模式——Q4 营收高于 Q1"""
    res = client.get("/api/indicators?department_id=1")
    data = res.json()["data"]
    q1 = [item["revenue"] for item in data if item["month"] in (1, 2, 3)]
    q4 = [item["revenue"] for item in data if item["month"] in (10, 11, 12)]
    assert sum(q4) / 3 > sum(q1) / 3  # Q4 平均值 > Q1 平均值


def test_data_department_consistency(client):
    """验证每个部门都有 24 条记录（12月 × 2年）"""
    for dept_id in [1, 2, 3]:
        res = client.get(f"/api/indicators?department_id={dept_id}")
        assert res.json()["total"] == 24
