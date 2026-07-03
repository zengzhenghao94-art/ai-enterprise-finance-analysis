"""NL2SQL API —— 自然语言查询转 SQL"""

import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..schemas import NL2SQLRequest, NL2SQLResponse

# 单次查询最大返回行数（防御 OOM）
MAX_RESULT_ROWS = 1000

router = APIRouter(prefix="/api/query", tags=["nl2sql"])

# 禁止的 SQL 关键字（安全校验）
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "TRUNCATE", "CREATE", "REPLACE", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "ATTACH", "DETACH", "PRAGMA",
]


def _load_system_prompt() -> str:
    # 项目根目录下的 prompts/
    prompt_path = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "nl2sql_system.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    # 内置默认 prompt（含完整 schema）
    return (
        "你是一个 SQLite SQL 生成助手。根据用户的自然语言输入，生成一条合法的 SQLite SELECT 语句。"
        "只输出 SQL，不要解释。\n\n"
        "重要规则：\n"
        "- 非查询拦截：如果用户输入是问候、闲聊、感谢等非数据查询内容，直接输出 [NOT_A_QUERY]，不要生成 SQL。\n"
        "- 年份字段 year 是整数，年份条件必须用字面数字如 `year = 2025`。\n"
        "- 禁止使用 strftime、date、julianday 等 SQLite 日期函数。\n"
        "- 月份字段 month 是整数 1-12。\n"
        "- 如果用户没有指定时间范围，默认查询 2025 年全年。\n\n"
        "## 数据库 Schema\n\n"
        "### departments(id INTEGER PK, name VARCHAR, manager VARCHAR)\n"
        "### financial_metrics(id INTEGER PK, department_id FK, year INT, month INT, "
        "revenue FLOAT, cost FLOAT, operating_expense FLOAT, net_profit FLOAT, "
        "cash_flow FLOAT, accounts_receivable FLOAT)\n"
        "### anomalies(id INTEGER PK, department_id FK, year INT, month INT, "
        "metric_name VARCHAR, metric_label VARCHAR, actual_value FLOAT, "
        "expected_range VARCHAR, deviation_pct FLOAT, severity VARCHAR, "
        "description TEXT, detected_at VARCHAR)\n\n"
        "常用派生指标：gross_margin = (revenue-cost)/revenue*100, "
        "profit_margin = net_profit/revenue*100, cost_ratio = cost/revenue\n"
        "使用 JOIN 获取 department_name。"
    )


def _validate_sql(sql: str) -> bool:
    """校验 SQL 只包含 SELECT 语句"""
    sql_upper = sql.strip().upper()
    # 去除非 ASCII 字符后再检查
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            return False
    if not sql_upper.startswith("SELECT"):
        return False
    return True


@router.post("/nl2sql", response_model=NL2SQLResponse)
def nl2sql(req: NL2SQLRequest, db: Session = Depends(get_db)):
    """自然语言查询：LLM 生成 SQL → 安全校验 → 执行 → 解释结果"""
    from ..services.llm_client import query_llm, estimate_tokens

    system_prompt = _load_system_prompt()

    # 构建 user prompt
    user_prompt = req.query
    if req.department_id is not None:
        user_prompt += f"\n限定部门 ID = {req.department_id}"

    # Step 1: LLM 生成 SQL
    try:
        raw_sql = query_llm(user_prompt, system_prompt=system_prompt).strip()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"查询处理失败: {e}")

    # 清理 SQL：提取 markdown 代码块内容（支持 ```sql 和 ```）
    md_match = re.search(r"```(?:sql)?\s*\n?(.*?)\n?```", raw_sql, re.DOTALL)
    if md_match:
        raw_sql = md_match.group(1).strip()
    # 去掉末尾分号
    raw_sql = raw_sql.rstrip(";").strip()

    sql_generated = raw_sql

    # Step 2: 非查询拦截 —— [NOT_A_QUERY] 可出现在 SQL 体内任意位置
    if "[NOT_A_QUERY]" in raw_sql.upper():
        return NL2SQLResponse(
            query=req.query,
            sql_generated="",
            result=[],
            explanation=(
                "您好！我是经营数据查询助手，可以帮您：\n"
                "- 📊 查指标：如「销售部 6 月收入」「各部门毛利率排名」\n"
                "- 📈 做分析：如「上半年净利润趋势」「哪个部门现金流最好」\n"
                "- ⚠️ 看异常：如「有哪些高危异常」「生产部异常汇总」\n\n"
                "请尝试输入具体的数据问题～"
            ),
            tokens_used=0,
        )
    if not _validate_sql(raw_sql):
        raise HTTPException(
            status_code=400,
            detail="SQL 安全校验未通过：仅支持 SELECT 查询，请重新描述需求",
        )

    # Step 3: 执行 SQL（限制最大行数防御 OOM）
    try:
        result_proxy = db.execute(text(raw_sql))
        rows = result_proxy.fetchmany(MAX_RESULT_ROWS)
        columns = list(result_proxy.keys())
        result = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(repr(e))
        raise HTTPException(
            status_code=400,
            detail="SQL 执行失败，请检查查询条件是否正确",
        )

    # Step 4: LLM 生成解释
    explanation = ""
    try:
        explain_prompt = (
            f"用户查询: {req.query}\n"
            f"查询结果（共 {len(result)} 条）:\n{result[:20]}\n\n"
            "请用 2-3 句话用中文解释这些数据说明了什么。"
        )
        explanation = query_llm(explain_prompt).strip()
    except Exception as e:
        print(repr(e))
        explanation = f"查询返回 {len(result)} 条记录。（注：AI 解释生成失败，以上为自动摘要）"

    tokens_used = estimate_tokens(user_prompt, system_prompt)

    return NL2SQLResponse(
        query=req.query,
        sql_generated=sql_generated,
        result=result,
        explanation=explanation,
        tokens_used=tokens_used,
    )
