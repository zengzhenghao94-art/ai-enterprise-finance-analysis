"""图表渲染器 —— 基于 Steep 设计系统的 matplotlib 图表

每个函数：入参数据 → 渲染图表 → 返回 PNG 文件路径。
所有函数接受 `output_dir` 参数，PNG 写入该目录。
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from .theme import COLORS, setup_matplotlib_rc

# 模块加载时应用样式（仅一次）
setup_matplotlib_rc()

# ---------- 颜色别名 ----------
BLUE = COLORS["steel_blue"]
CYAN = COLORS["cyan"]
CRIMSON = COLORS["crimson"]
INK = COLORS["ink"]
ASH = COLORS["ash"]
GRAPHITE = COLORS["graphite"]
DO = COLORS["dove"]


def render_trend_chart(
    metrics: list[dict],
    year: int,
    output_dir: Path,
    filename: str = "trend.png",
) -> Path:
    """月度趋势折线图 —— 收入 / 成本 / 净利润 三条线

    Args:
        metrics: [{"month": 1, "revenue": ..., "cost": ..., "net_profit": ...}, ...]
        year: 年份（图表标题用）
        output_dir: 输出目录
        filename: 输出文件名

    Returns:
        生成的 PNG 文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename

    months = [m["month"] for m in metrics]
    revenues = [m["revenue"] for m in metrics]
    costs = [m["cost"] for m in metrics]
    profits = [m["net_profit"] for m in metrics]

    fig, ax = plt.subplots(figsize=(8, 3.2))
    fig.patch.set_facecolor(COLORS["pure_white"])

    ax.plot(months, revenues, color=BLUE, linewidth=2.5, marker="o",
            markersize=5, label="营业收入", zorder=3)
    ax.plot(months, costs, color=CYAN, linewidth=2.0, marker="s",
            markersize=4.5, label="营业成本", zorder=2)
    ax.plot(months, profits, color=GRAPHITE, linewidth=2.0, marker="^",
            markersize=4.5, label="净利润", zorder=1)

    ax.set_title(f"{year}年 月度经营指标趋势", fontsize=14, fontweight="bold",
                 color=INK, pad=14)
    ax.set_xlabel("月份", color=GRAPHITE)
    ax.set_ylabel("万元", color=GRAPHITE)
    ax.set_xticks(months)
    ax.set_xticklabels([f"{m}月" for m in months])
    ax.legend()

    fig.tight_layout()
    fig.savefig(str(path), dpi=200, bbox_inches="tight", facecolor=COLORS["pure_white"])
    plt.close(fig)
    return path


def render_kpi_comparison(
    dept_metrics: list[dict],
    output_dir: Path,
    filename: str = "kpi_comparison.png",
) -> Path:
    """部门 KPI 对比分组柱状图

    Args:
        dept_metrics: [{"dept_name": "销售部", "revenue": ..., "cost": ...,
                         "net_profit": ..., "gross_margin": ..., "profit_margin": ...}, ...]
        output_dir: 输出目录
        filename: 输出文件名

    Returns:
        生成的 PNG 文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename

    dept_names = [d["dept_name"] for d in dept_metrics]
    n_depts = len(dept_names)
    x = np.arange(n_depts)
    width = 0.25

    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    fig.patch.set_facecolor(COLORS["pure_white"])

    # 三个指标：收入 / 成本 / 净利润
    bars1 = ax.bar(x - width, [d["revenue"] for d in dept_metrics],
                   width, color=BLUE, alpha=0.9, label="营业收入")
    bars2 = ax.bar(x, [d["cost"] for d in dept_metrics],
                   width, color=CYAN, alpha=0.9, label="营业成本")
    bars3 = ax.bar(x + width, [d["net_profit"] for d in dept_metrics],
                   width, color=GRAPHITE, alpha=0.75, label="净利润")

    ax.set_title("部门核心指标对比", fontsize=14, fontweight="bold", color=INK, pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(dept_names)
    ax.set_ylabel("万元", color=GRAPHITE)
    ax.legend()

    # 柱顶标签（仅收入柱）
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., h + 5,
                f"{h:.0f}", ha="center", va="bottom", fontsize=9, color=GRAPHITE)

    fig.tight_layout()
    fig.savefig(str(path), dpi=200, bbox_inches="tight", facecolor=COLORS["pure_white"])
    plt.close(fig)
    return path


def render_anomaly_chart(
    anomalies: list[dict],
    output_dir: Path,
    filename: str = "anomaly.png",
) -> Path:
    """异常指标分布散点图

    Args:
        anomalies: [{"metric_label": "毛利率", "dept_name": "生产部",
                      "deviation_pct": -19.9, "severity": "high"}, ...]
        output_dir: 输出目录
        filename: 输出文件名

    Returns:
        生成的 PNG 文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename

    if not anomalies:
        # 无异常时生成空图 + 文字
        fig, ax = plt.subplots(figsize=(8, 3))
        fig.patch.set_facecolor(COLORS["pure_white"])
        ax.text(0.5, 0.5, "本月无异常 ✓", ha="center", va="center",
                fontsize=18, color=GRAPHITE, transform=ax.transAxes)
        ax.axis("off")
        fig.savefig(str(path), dpi=200, bbox_inches="tight", facecolor=COLORS["pure_white"])
        plt.close(fig)
        return path

    fig, ax = plt.subplots(figsize=(7.5, 3.5))
    fig.patch.set_facecolor(COLORS["pure_white"])

    # Y 轴：指标类别（用标签代替数字）
    labels = sorted(set(a["metric_label"] for a in anomalies))
    label_to_y = {label: i for i, label in enumerate(labels)}

    xs = []
    ys = []
    colors = []
    sizes = []
    annotations = []

    for a in anomalies:
        xs.append(abs(a["deviation_pct"]))
        ys.append(label_to_y[a["metric_label"]])
        colors.append(CRIMSON if a["severity"] == "high" else
                      ("#f97316" if a["severity"] == "medium" else "#eab308"))
        sizes.append(140 if a["severity"] == "high" else (100 if a["severity"] == "medium" else 60))
        annotations.append(f"{a.get('dept_name', '')}-{a['metric_label']}\n{a['deviation_pct']:+.1f}%")

    ax.scatter(xs, ys, c=colors, s=sizes, alpha=0.8, edgecolors="white", linewidths=1.5, zorder=3)

    # 标注
    for i, (xi, yi, ann) in enumerate(zip(xs, ys, annotations)):
        ax.annotate(ann, (xi, yi), textcoords="offset points", xytext=(8, 5),
                    fontsize=9, color=ASH)

    ax.set_yticks(list(label_to_y.values()))
    ax.set_yticklabels(list(label_to_y.keys()))
    ax.set_xlabel("偏离幅度 (%)", color=GRAPHITE)
    ax.set_title("异常指标分布", fontsize=14, fontweight="bold", color=INK, pad=14)
    ax.set_xlim(left=0)

    # 添加 severity 图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=CRIMSON, markersize=10, label="高风险 (High)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#f97316", markersize=8, label="中风险 (Medium)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    fig.tight_layout()
    fig.savefig(str(path), dpi=200, bbox_inches="tight", facecolor=COLORS["pure_white"])
    plt.close(fig)
    return path


def render_dept_radar(
    dept_metrics: list[dict],
    output_dir: Path,
    filename: str = "dept_radar.png",
) -> Path:
    """部门雷达图 —— 多维度经营能力对比

    Args:
        dept_metrics: [{"dept_name": "销售部", "gross_margin": ..., "profit_margin": ...,
                         "revenue_rank": ..., "cash_flow_ratio": ..., "cost_control": ...}, ...]
        output_dir: 输出目录
        filename: 输出文件名

    Returns:
        生成的 PNG 文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename

    if not dept_metrics:
        return path

    dimensions = list(dept_metrics[0].keys())
    dimensions.remove("dept_name")
    n_dims = len(dimensions)
    if n_dims < 3:
        return path

    # 雷达图角度
    angles = np.linspace(0, 2 * np.pi, n_dims, endpoint=False).tolist()
    angles += angles[:1]  # 闭环

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(COLORS["pure_white"])
    ax.set_facecolor(COLORS["pure_white"])

    colors_cycle = [BLUE, CYAN, GRAPHITE]

    for idx, dept in enumerate(dept_metrics):
        values = [dept[dim] for dim in dimensions]
        values += values[:1]  # 闭环
        color = colors_cycle[idx % len(colors_cycle)]

        ax.fill(angles, values, alpha=0.08, color=color)
        ax.plot(angles, values, linewidth=2, color=color, label=dept["dept_name"])
        ax.scatter(angles[:-1], values[:-1], s=40, color=color, zorder=3)

    # 维度标签
    dim_labels = [d.replace("_", " ") for d in dimensions]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dim_labels, fontsize=10, color=ASH)
    ax.set_yticklabels([])

    # 网格样式
    ax.spines["polar"].set_color(DO)
    ax.spines["polar"].set_alpha(0.4)
    ax.grid(color=DO, alpha=0.3, linewidth=0.5)

    ax.set_title("部门经营能力雷达", fontsize=14, fontweight="bold", color=INK, pad=20)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=len(dept_metrics))

    fig.tight_layout()
    fig.savefig(str(path), dpi=200, bbox_inches="tight", facecolor=COLORS["pure_white"])
    plt.close(fig)
    return path
