"""报告打包器 —— ZIP 打包 + PDF（可选）"""

import zipfile
import shutil
from pathlib import Path


def package_zip(
    html_path: Path,
    chart_dir: Path,
    output_dir: Path,
    filename: str = "简报.zip",
) -> Path:
    """将 HTML + 图表目录打包为 ZIP。

    Args:
        html_path: 报告 HTML 文件路径
        chart_dir: 图表 PNG 所在目录
        output_dir: ZIP 输出目录
        filename: ZIP 文件名

    Returns:
        ZIP 文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / filename

    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        # 写入 HTML（根目录）
        zf.write(str(html_path), html_path.name)

        # 写入 CSS 文件
        css_content = """/* Steep Design System — Report Styles */
:root {
  --obsidian: #000000; --ink: #17191c; --ash: #4c4c4c;
  --graphite: #777b86; --slate: #8b8c8d; --dove: #a3a6af;
  --fog: #f7f7f8; --white: #ffffff;
  --blue: #1e40af; --cyan: #0891b2; --crimson: #dc2626;
}
body { font-family: 'Inter', 'Noto Sans SC', sans-serif; font-size: 16px; color: var(--ink); max-width: 1200px; margin: 40px auto; padding: 0 32px; }
h1 { font-family: 'Noto Serif', serif; font-size: 44px; font-weight: 400; }
h2 { font-family: 'Noto Serif', serif; font-size: 26px; margin-top: 80px; }
img { max-width: 100%; border-radius: 12px; margin: 24px 0; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 10px 14px; border-bottom: 2px solid var(--ink); font-size: 13px; text-transform: uppercase; }
td { padding: 10px 14px; border-bottom: 1px solid var(--dove); }
@media print { body { font-size: 13px; } }
"""
        # 将 CSS 写入临时位置再打包
        css_temp = output_dir / "report.css"
        css_temp.write_text(css_content, encoding="utf-8")
        zf.write(str(css_temp), "report.css")
        css_temp.unlink(missing_ok=True)  # 打包完立即清理，不留残留文件

        # 写入图表目录
        if chart_dir.exists():
            for png_file in sorted(chart_dir.glob("*.png")):
                zf.write(str(png_file), f"charts/{png_file.name}")

    return zip_path


def package_pdf(html_path: Path, output_dir: Path, filename: str = "简报.pdf") -> Path | None:
    """使用 wkhtmltopdf 将 HTML 转为 PDF（可选，需要安装 wkhtmltopdf）。

    Args:
        html_path: HTML 文件路径
        output_dir: 输出目录
        filename: PDF 文件名

    Returns:
        PDF 文件路径，如果 wkhtmltopdf 不可用则返回 None
    """
    if not shutil.which("wkhtmltopdf"):
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / filename

    import subprocess
    subprocess.run(
        [
            "wkhtmltopdf",
            "--enable-local-file-access",
            "--page-size", "A4",
            "--margin-top", "15mm",
            "--margin-bottom", "15mm",
            "--margin-left", "12mm",
            "--margin-right", "12mm",
            str(html_path),
            str(pdf_path),
        ],
        check=True,
        capture_output=True,
    )
    return pdf_path
