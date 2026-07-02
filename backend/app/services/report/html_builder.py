"""HTML 报告构建器 —— Steep 设计 + Column 瑞士网格

组装 clean HTML：CSS 内联 + 图表 `<img>` 外引 + Markdown 正文。
"""

from pathlib import Path
import re


CSS = r"""/* ============================================================
   Steep Design System — Report Styles
   基于 docs/DESIGN.md 设计 token
   ============================================================ */

:root {
  /* 灰度骨架 */
  --obsidian: #000000;
  --ink:      #17191c;
  --ash:      #4c4c4c;
  --graphite: #777b86;
  --slate:    #8b8c8d;
  --dove:     #a3a6af;
  --fog:      #f7f7f8;
  --white:    #ffffff;

  /* 数据色彩 */
  --blue:     #1e40af;
  --cyan:     #0891b2;
  --wash:     #dbeafe;
  --sky-wash: #d3e3fc;
  --crimson:  #dc2626;

  /* 间距 & 形状 */
  --radius-card:  24px;
  --radius-img:   12px;
  --radius-btn:   9999px;
  --card-padding: 24px;
  --section-gap:  80px;
  --max-width:    1200px;
}

/* ---------- Reset & Base ---------- */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: var(--ink);
  background: var(--white);
  -webkit-font-smoothing: antialiased;
}

/* ---------- Typography ---------- */
h1 { font-family: 'Noto Serif', 'Noto Serif CJK SC', 'SimSun', serif;
     font-size: 44px; font-weight: 400; line-height: 1.1; margin-bottom: 16px; }
h2 { font-family: 'Noto Serif', 'Noto Serif CJK SC', 'SimSun', serif;
     font-size: 26px; font-weight: 450; line-height: 1.18; margin-top: var(--section-gap); margin-bottom: 12px;
     padding-bottom: 10px; border-bottom: 2px solid var(--fog); }
h3 { font-size: 18px; font-weight: 500; line-height: 1.4; margin-top: 32px; margin-bottom: 8px; color: var(--ink); }
h4 { font-size: 16px; font-weight: 500; margin-top: 20px; margin-bottom: 6px; color: var(--ash); }

p  { margin-bottom: 12px; color: var(--ink); line-height: 1.65; }
ul, ol { padding-left: 24px; margin-bottom: 12px; }
li { margin-bottom: 6px; line-height: 1.5; }

strong { font-weight: 600; color: var(--ink); background: linear-gradient(180deg, transparent 60%, var(--wash) 60%); padding: 0 2px; }

/* ---------- Layout ---------- */
.page {
  max-width: var(--max-width);
  margin: 40px auto 80px;
  padding: 0 32px;
}

.header {
  padding: 48px 0 40px;
  border-bottom: 1px solid var(--dove);
  margin-bottom: var(--section-gap);
}

.header h1 { margin-bottom: 8px; }
.header .meta { color: var(--graphite); font-size: 16px; }

/* ---------- KPI Cards ---------- */
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 32px; }

.kpi-card {
  background: var(--white);
  border: 1px solid var(--dove);
  border-radius: var(--radius-card);
  padding: var(--card-padding);
}

.kpi-card .label { font-size: 14px; color: var(--graphite); margin-bottom: 8px; }
.kpi-card .value { font-size: 44px; font-weight: 400; line-height: 1.1; color: var(--ink); }
.kpi-card .unit  { font-size: 16px; color: var(--ash); margin-left: 4px; }

.kpi-card.warm { background: var(--wash); border-color: transparent; }

/* ============================================================
   数据故事 — 全宽图表区块（每个图表都是一个独立"故事"）
   ============================================================ */

.data-story {
  position: relative;
  margin: 48px 0;
  padding: 36px 40px;
  border-radius: var(--radius-card);
  background: var(--white);
  border: 1px solid var(--dove);
  overflow: hidden;
}

/* 故事标题区 */
.data-story .story-head {
  margin-bottom: 28px;
  padding-left: 14px;
  border-left: 3px solid var(--blue);
  position: relative;
  z-index: 2;
}

.data-story .story-head .story-index {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  color: var(--blue);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.data-story .story-head h3 {
  font-family: 'Noto Serif', 'Noto Serif CJK SC', 'SimSun', serif;
  font-size: 24px;
  font-weight: 400;
  line-height: 1.2;
  color: var(--ink);
  margin: 0 0 6px 0;
}

.data-story .story-head .story-subtitle {
  font-size: 16px;
  color: var(--ash);
  line-height: 1.5;
  max-width: 640px;
}

/* 图表图片 — 居中 + 最大宽度约束 */
.data-story .story-chart {
  position: relative;
  z-index: 2;
  max-width: 780px;
  margin: 0 auto;
}

.data-story .story-chart img {
  width: 100%;
  max-height: 440px;
  object-fit: contain;
  border-radius: var(--radius-img);
}

.data-story .story-footnote {
  margin-top: 12px;
  font-size: 13px;
  font-weight: 500;
  color: var(--graphite);
  text-align: center;
  letter-spacing: 0.04em;
  position: relative;
  z-index: 2;
}

/* ---- 背景纹理：每个故事区块不同的 SVG/CSS 图案 ---- */

/* Trend — Ledger lines: 瑞士账簿横线，Fog on White */
.data-story.story-trend {
  background-color: var(--white);
  background-image:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 31px,
      var(--fog) 31px,
      var(--fog) 32px
    );
}

/* KPI — Dot grid: Swiss 网格点阵，Dove 小圆点 */
.data-story.story-kpi {
  background-color: var(--white);
  background-image:
    radial-gradient(circle, var(--dove) 1px, transparent 1px);
  background-size: 28px 28px;
}

/* Anomaly — Alert bars: 微妙斜条纹警示区，Blue Wash 底色 */
.data-story.story-anomaly {
  background-color: var(--wash);
  background-image:
    repeating-linear-gradient(
      -2deg,
      transparent,
      transparent 48px,
      rgba(30, 64, 175, 0.04) 48px,
      rgba(30, 64, 175, 0.04) 50px
    );
}

/* Radar — Concentric rings: 雷达/靶心隐喻，Sky Wash */
.data-story.story-radar {
  background-color: var(--white);
  background-image:
    radial-gradient(ellipse at 50% 50%, var(--sky-wash) 0%, transparent 55%),
    radial-gradient(circle at 50% 50%, transparent 58%, var(--dove) 58.5%, transparent 59%),
    radial-gradient(circle at 50% 50%, transparent 72%, var(--dove) 72.5%, transparent 73%);
  background-size: 100% 100%;
}

/* 故事之间的分隔装饰 */
.data-story + .data-story {
  margin-top: 64px;
}

/* ---------- Anomaly Table ---------- */
.anomaly-list { margin: 16px 0 32px; }

.anomaly-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  margin-bottom: 8px;
  border-radius: 12px;
  background: var(--fog);
  border-left: 4px solid var(--dove);
}

.anomaly-item.severity-high   { border-left-color: var(--crimson); background: #fef2f2; }
.anomaly-item.severity-medium { border-left-color: #f97316; background: #fff7ed; }
.anomaly-item.severity-low    { border-left-color: #eab308; background: #fefce8; }

.anomaly-item .sev-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 8px;
  white-space: nowrap;
}
.sev-badge.high   { background: var(--crimson); color: white; }
.sev-badge.medium { background: #f97316; color: white; }
.sev-badge.low    { background: #eab308; color: white; }

.anomaly-item .anom-body { flex: 1; font-size: 15px; }

/* ---------- SQL / Data Block (Column Swiss ledger gene) ---------- */
code, pre {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

pre {
  background: var(--fog);
  border-radius: 12px;
  padding: 20px 24px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
  margin: 16px 0;
}

hr {
  border: none;
  height: 1px;
  background: var(--dove);
  margin: 32px 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0 32px;
  font-size: 15px;
}

thead th {
  text-align: left;
  padding: 10px 14px;
  border-bottom: 2px solid var(--ink);
  font-weight: 500;
  font-size: 13px;
  color: var(--graphite);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--dove);
  font-variant-numeric: tabular-nums;
}

tbody tr:nth-child(even) { background: var(--fog); }

/* ---------- Footer ---------- */
.footer {
  margin-top: var(--section-gap);
  padding-top: 24px;
  border-top: 1px solid var(--dove);
  font-size: 14px;
  color: var(--graphite);
}

/* ---------- Print ---------- */
@media print {
  body { font-size: 13px; }
  .page { max-width: 100%; margin: 0; padding: 0 16px; }
  .kpi-grid { grid-template-columns: repeat(3, 1fr); }
  h1 { font-size: 32px; }
  h2 { font-size: 22px; }
  .data-story { margin: 48px 0; padding: 40px 32px; }
  .data-story .story-head h3 { font-size: 22px; }
  .section-gap { break-before: page; }
}
"""


def _md_to_html(md_text: str) -> str:
    """轻量 Markdown → HTML 转换。不引入第三方库，处理常见模式。"""
    lines = md_text.split("\n")
    html_lines = []
    in_code_block = False
    in_list = False

    for line in lines:
        # Code block
        if line.strip().startswith("```"):
            if in_code_block:
                html_lines.append("</code></pre>")
                in_code_block = False
            else:
                html_lines.append("<pre><code>")
                in_code_block = True
            continue
        if in_code_block:
            html_lines.append(line)
            continue

        # Headings
        if line.startswith("#### "):
            html_lines.append(f"<h4>{line[5:]}</h4>")
            continue
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
            continue
        if line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
            continue
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
            continue

        # Horizontal rule
        if line.strip() == "---":
            html_lines.append("<hr>")
            continue

        # List items
        li_match = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        ordered_match = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if li_match:
            if not in_list:
                html_lines.append("<ul>")
                in_list = "ul"
            html_lines.append(f"<li>{li_match.group(2)}</li>")
            continue
        elif ordered_match:
            if not in_list:
                html_lines.append("<ol>")
                in_list = "ol"
            html_lines.append(f"<li>{ordered_match.group(2)}</li>")
            continue
        else:
            if in_list:
                html_lines.append(f"</{in_list}>")
                in_list = None

        # Bold & italic
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)

        # Inline code
        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)

        # Paragraph
        if line.strip():
            html_lines.append(f"<p>{line}</p>")
        else:
            html_lines.append("")

    if in_list:
        html_lines.append(f"</{in_list}>")
    if in_code_block:
        html_lines.append("</code></pre>")

    return "\n".join(html_lines)


def build_report_html(
    report_content: str,
    chart_paths: dict[str, str],
    metadata: dict,
    output_dir: Path,
    filename: str = "report.html",
) -> Path:
    """组装完整的报告 HTML 文件。

    Args:
        report_content: LLM 生成的 Markdown 报告正文
        chart_paths: {"trend": "charts/trend.png", "kpi": "charts/kpi_comparison.png", ...}
                     值相对于 HTML 文件的路径
        metadata: {"title": ..., "year": 2025, "month": 6, "dept": "全公司", "generated_at": "..."}
        output_dir: 输出目录
        filename: HTML 文件名

    Returns:
        生成的 HTML 文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / filename

    body_html = _md_to_html(report_content)

    # ---- 数据故事区块（每张图表 = 一个全宽故事卡片 + 专属背景纹理） ----
    chart_stories = [
        {
            "key": "trend",
            "path": chart_paths.get("trend", ""),
            "css_class": "story-trend",
            "index": "01",
            "title": "营收·成本·利润 月度趋势",
            "subtitle": "全年 12 个月三条核心经营线走势。关注收入是否匹配成本增长、利润曲线是否在年末收敛。",
            "footnote": "图 1 · 折线图",
        },
        {
            "key": "kpi",
            "path": chart_paths.get("kpi", ""),
            "css_class": "story-kpi",
            "index": "02",
            "title": "部门核心指标横向对比",
            "subtitle": "收入、成本、净利润三项指标跨部门并列。深蓝色柱为营收，青色柱为成本，灰色柱为净利润。" + ("单部门模式下此项不适用。" if not chart_paths.get("kpi") else ""),
            "footnote": "图 2 · 分组柱状图",
        },
        {
            "key": "anomaly",
            "path": chart_paths.get("anomaly", ""),
            "css_class": "story-anomaly",
            "index": "03",
            "title": "异常指标分布",
            "subtitle": "每个圆点代表一条被 Isolation Forest + Z‑score 交叉验证的异常记录。红色 = 高风险（偏离 > 30%），橙色 = 中风险。圆点越大越危险。" if chart_paths.get("anomaly") else "本月未检测到异常指标，经营数据均在正常波动区间内。",
            "footnote": "图 3 · 散点分布图",
        },
        {
            "key": "radar",
            "path": chart_paths.get("radar", ""),
            "css_class": "story-radar",
            "index": "04",
            "title": "部门经营能力雷达",
            "subtitle": "五维度综合评估——毛利能力、净利效率、现金流健康度、费用控制、收入规模。面积越大越均衡。" + ("需要至少 3 个部门才能生成雷达图。" if not chart_paths.get("radar") else ""),
            "footnote": "图 4 · 雷达图",
        },
    ]

    chart_blocks = ""
    for story in chart_stories:
        if not story["path"]:
            continue  # 没有图就跳过这个区块
        chart_blocks += f"""<!-- {story['title']} -->
    <div class="data-story {story['css_class']}">
      <div class="story-head">
        <div class="story-index">{story['index']} — 数据故事</div>
        <h3>{story['title']}</h3>
        <p class="story-subtitle">{story['subtitle']}</p>
      </div>
      <div class="story-chart">
        <img src="{story['path']}" alt="{story['title']}">
      </div>
      <div class="story-footnote">{story['footnote']}</div>
    </div>
    """

    # 异常列表（如果 metadata 包含）
    anomaly_html = ""
    if metadata.get("anomalies"):
        anomaly_html += '<div class="anomaly-list">\n'
        for a in metadata["anomalies"]:
            sev = a.get("severity", "low")
            anomaly_html += f"""      <div class="anomaly-item severity-{sev}">
        <span class="sev-badge {sev}">{sev.upper()}</span>
        <span class="anom-body"><strong>{a.get('dept_name', '')} — {a.get('metric_label', '')}</strong>：实际 {a.get('actual_value', '—')}，预期 {a.get('expected_range', '—')}，偏离 <span style="color:var(--crimson)">{a.get('deviation_pct', 0):+.1f}%</span></span>
      </div>
    """
        anomaly_html += '    </div>\n'

    # 部门标签
    dept_label = metadata.get("dept", "全公司")
    if dept_label == "全公司":
        dept_label = "全公司"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{metadata.get('title', '经营分析简报')}</title>
  <style>{CSS}</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div class="header">
    <h1>{metadata.get('title', '经营分析简报')}</h1>
    <div class="meta">
      {dept_label} · {metadata.get('year', '—')}年{metadata.get('month', '—')}月 · 生成于 {metadata.get('generated_at', '—')}
    </div>
  </div>

  <!-- Data Stories Section -->
  <h2>数据总览</h2>
  {chart_blocks}

  <!-- Anomaly Section -->
  { ('<h2>异常指标预警</h2>' + anomaly_html) if anomaly_html else '' }

  <!-- Report Body -->
  <h2>经营分析</h2>
  {body_html}

  <!-- Footer -->
  <div class="footer">
    <p>本报告由 AI 经营分析平台自动生成 · 数据来源：企业经营数据库 · 仅供参考，不构成决策建议</p>
  </div>

</div>
</body>
</html>"""

    html_path.write_text(html, encoding="utf-8")
    return html_path
