"""报告导出服务——图表渲染 + HTML 组装 + 打包"""

from .theme import COLORS, setup_matplotlib_rc
from .charts import (
    render_trend_chart,
    render_kpi_comparison,
    render_anomaly_chart,
    render_dept_radar,
)
from .html_builder import build_report_html
from .packager import package_zip

__all__ = [
    "COLORS",
    "setup_matplotlib_rc",
    "render_trend_chart",
    "render_kpi_comparison",
    "render_anomaly_chart",
    "render_dept_radar",
    "build_report_html",
    "package_zip",
]
