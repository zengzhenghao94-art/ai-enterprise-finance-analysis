"""数据库模型定义 —— SQLAlchemy ORM

三张表：
1. departments       — 部门
2. financial_metrics — 月度经营指标（6 个原子指标）
3. anomalies         — 异常检测记录

设计原则：只存原子指标，派生指标（毛利、毛利率等）由 NL2SQL 引擎动态计算。
"""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="部门名称")
    manager = Column(String(20), nullable=False, comment="负责人")

    # 关系
    metrics = relationship("FinancialMetric", back_populates="department")
    anomalies = relationship("Anomaly", back_populates="department")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"


class FinancialMetric(Base):
    """月度经营指标 — 6 个原子指标，不存派生指标"""

    __tablename__ = "financial_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, comment="所属部门")
    year = Column(Integer, nullable=False, comment="年份")
    month = Column(Integer, nullable=False, comment="月份 1-12")

    # ---- 6 个原子指标 ----
    revenue = Column(Float, nullable=False, comment="营业收入（万元）")
    cost = Column(Float, nullable=False, comment="营业成本（万元）")
    operating_expense = Column(Float, nullable=False, comment="运营费用（万元），管理+销售+财务费用合计")
    net_profit = Column(Float, nullable=False, comment="净利润（万元）")
    cash_flow = Column(Float, nullable=False, comment="经营现金流（万元）")
    accounts_receivable = Column(Float, nullable=False, comment="应收账款（万元）")

    # 约束
    __table_args__ = (
        UniqueConstraint("department_id", "year", "month", name="uq_metric_dept_ym"),
    )

    # 关系
    department = relationship("Department", back_populates="metrics")

    def __repr__(self):
        return (
            f"<FinancialMetric(dept={self.department_id}, "
            f"{self.year}-{self.month:02d}, revenue={self.revenue})>"
        )


class Anomaly(Base):
    """异常检测记录 —— Isolation Forest 输出 + LLM 解释"""

    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, comment="所属部门")
    year = Column(Integer, nullable=False, comment="异常年份")
    month = Column(Integer, nullable=False, comment="异常月份")
    metric_name = Column(String(50), nullable=False, comment="异常指标字段名，如 gross_margin")
    metric_label = Column(String(20), nullable=False, comment="指标中文标签，如 毛利率")
    actual_value = Column(Float, nullable=False, comment="实际值")
    expected_range = Column(String(30), nullable=False, comment="预期范围，如 25.0-35.0")
    deviation_pct = Column(Float, nullable=False, comment="偏离百分比，负值=低于预期")
    severity = Column(String(10), nullable=False, default="medium", comment="严重程度: high/medium/low")
    description = Column(Text, nullable=True, comment="LLM 生成的异常解释")
    detected_at = Column(String(30), nullable=False, comment="检测时间 ISO 格式")

    # 关系
    department = relationship("Department", back_populates="anomalies")

    def __repr__(self):
        return (
            f"<Anomaly(dept={self.department_id}, "
            f"{self.year}-{self.month:02d}, {self.metric_label}, severity={self.severity})>"
        )
