"""NL2SQL API —— 自然语言查询转 SQL"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..schemas import NL2SQLRequest, NL2SQLResponse

router = APIRouter(prefix="/api/query", tags=["nl2sql"])

# 禁止的 SQL 关键字（安全校验）
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "TRUNCATE", "CREATE", "REPLACE", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "ATTACH", "DETACH", "PRAGMA",
]


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "nl2sql_system.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    # 内置默认 prompt（含完整 schema）
    return (
        "你是一个 SQLite SQL 生成助手。根据用户的自然语言输入，生成一条合法的 SQLite SELECT 语句。"
        "只输出 SQL，不要解释。\n\n"
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
        raise HTTPException(status_code=503, detail=str(e))

    # 清理 SQL（去掉可能的 markdown 代码块标记）
    if raw_sql.startswith("```"):
        lines = raw_sql.split("\n")
        # 去掉首行 ```sql 和末行 ```
        sql_lines = [l for l in lines if not l.startswith("```")]
        raw_sql = "\n".join(sql_lines).strip()
    # 去掉末尾分号
    raw_sql = raw_sql.rstrip(";").strip()

    sql_generated = raw_sql

    # Step 2: 安全校验
    if not _validate_sql(raw_sql):
        raise HTTPException(
            status_code=400,
            detail=f"SQL 安全校验未通过：只允许 SELECT。生成: {raw_sql}",
        )

    # Step 3: 执行 SQL
    try:
        result_proxy = db.execute(text(raw_sql))
        rows = result_proxy.fetchall()
        columns = list(result_proxy.keys())
        result = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(repr(e))
        raise HTTPException(
            status_code=400,
            detail=f"SQL 执行失败: {repr(e)}\nSQL: {raw_sql}",
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
        explanation = f"查询返回 {len(result)} 条记录。"
    finally:
        pass

    tokens_used = estimate_tokens(user_prompt, system_prompt)

    return NL2SQLResponse(
        query=req.query,
        sql_generated=sql_generated,
        result=result,
        explanation=explanation,
        tokens_used=tokens_used,
    )
