"""matplotlib 全局样式 —— 基于 Steep 设计系统

本模块设置 matplotlib rcParams，使所有图表输出对齐 Steep 色板。
导入即生效：`from .theme import setup_matplotlib_rc; setup_matplotlib_rc()`
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

# ============================================================
# Steep 色板
# ============================================================

COLORS = {
    # 灰度骨架
    "obsidian":   "#000000",  # 锐利细线
    "ink":        "#17191c",  # 主文本
    "ash":        "#4c4c4c",  # 次级文本
    "graphite":   "#777b86",  # 三级文本 / 坐标轴标签
    "slate":      "#8b8c8d",  # 图标 / 弱链接
    "dove":       "#a3a6af",  # 网格线 / placeholder
    "fog":        "#f7f7f8",  # 次级背景
    "pure_white": "#ffffff",  # 页面 / 卡片底色

    # 数据色彩
    "steel_blue": "#1e40af",  # 主线
    "cyan":       "#0891b2",  # 辅线
    "blue_wash":  "#dbeafe",  # 暖调数据背景
    "sky_wash":   "#d3e3fc",  # 冷调数据背景
    "crimson":    "#dc2626",  # 异常标记
}

# ============================================================
# 字体发现
# ============================================================

def _find_cjk_font() -> str:
    """在系统中查找可用的 CJK 字体"""
    candidates = [
        "Noto Sans SC", "Noto Sans CJK SC", "Source Han Sans SC",
        "Microsoft YaHei", "SimHei", "PingFang SC",
        "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
        "Noto Serif CJK SC", "Source Han Serif SC",
        "SimSun", "STSong",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return "sans-serif"


def _find_mono_font() -> str:
    """在系统中查找可用的等宽字体"""
    candidates = ["JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas", "Courier New"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return "monospace"


_SANS_FONT = _find_cjk_font()
_SERIF_FONT = _find_cjk_font()  # 先用找到的 CJK sans 兜底
_MONO_FONT = _find_mono_font()

# 尝试找到衬线 CJK 字体
for _serif_candidate in ["Noto Serif CJK SC", "Source Han Serif SC", "SimSun", "STSong"]:
    _available = {f.name for f in fm.fontManager.ttflist}
    if _serif_candidate in _available:
        _SERIF_FONT = _serif_candidate
        break


# ============================================================
# rcParams 设置
# ============================================================

def setup_matplotlib_rc():
    """应用 Steep 风格的 matplotlib 全局样式。导入后调用一次即可。"""

    # ---------- 字体 ----------
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.sans-serif"] = [_SANS_FONT, "Inter", "DejaVu Sans"]
    matplotlib.rcParams["font.serif"] = [_SERIF_FONT, "DejaVu Serif"]
    matplotlib.rcParams["font.monospace"] = [_MONO_FONT, "DejaVu Sans Mono"]
    matplotlib.rcParams["font.size"] = 11

    # ---------- 图表尺寸 & DPI ----------
    matplotlib.rcParams["figure.dpi"] = 150
    matplotlib.rcParams["savefig.dpi"] = 200
    matplotlib.rcParams["savefig.bbox"] = "tight"
    matplotlib.rcParams["savefig.facecolor"] = COLORS["pure_white"]
    matplotlib.rcParams["savefig.edgecolor"] = "none"

    # ---------- 坐标轴 ----------
    matplotlib.rcParams["axes.facecolor"] = COLORS["pure_white"]
    matplotlib.rcParams["axes.edgecolor"] = COLORS["slate"]
    matplotlib.rcParams["axes.linewidth"] = 0.8
    matplotlib.rcParams["axes.spines.top"] = False
    matplotlib.rcParams["axes.spines.right"] = False
    matplotlib.rcParams["axes.titlesize"] = 14
    matplotlib.rcParams["axes.titleweight"] = "normal"
    matplotlib.rcParams["axes.titlecolor"] = COLORS["ink"]
    matplotlib.rcParams["axes.labelcolor"] = COLORS["graphite"]
    matplotlib.rcParams["axes.labelsize"] = 11

    # ---------- 网格 ----------
    matplotlib.rcParams["axes.grid"] = True
    matplotlib.rcParams["axes.grid.axis"] = "y"
    matplotlib.rcParams["grid.color"] = COLORS["dove"]
    matplotlib.rcParams["grid.alpha"] = 0.3
    matplotlib.rcParams["grid.linewidth"] = 0.5

    # ---------- 刻度 ----------
    matplotlib.rcParams["xtick.color"] = COLORS["graphite"]
    matplotlib.rcParams["xtick.labelsize"] = 10
    matplotlib.rcParams["ytick.color"] = COLORS["graphite"]
    matplotlib.rcParams["ytick.labelsize"] = 10

    # ---------- 图例 ----------
    matplotlib.rcParams["legend.frameon"] = True
    matplotlib.rcParams["legend.fancybox"] = True
    matplotlib.rcParams["legend.framealpha"] = 0.9
    matplotlib.rcParams["legend.edgecolor"] = COLORS["dove"]
    matplotlib.rcParams["legend.fontsize"] = 10
    matplotlib.rcParams["legend.title_fontsize"] = 10

    # ---------- 线条 ----------
    matplotlib.rcParams["lines.linewidth"] = 2.0
    matplotlib.rcParams["lines.markersize"] = 6

    print(f"[theme] matplotlib Steep 主题已应用，CJK 字体: {_SANS_FONT}, 等宽: {_MONO_FONT}")
