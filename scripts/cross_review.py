"""异模审查脚本 — 通义千问审查 DeepSeek 产出

用法：
    python cross_review.py <内容文件>
    echo "内容" | python cross_review.py --stdin
    python cross_review.py <文件> --model qwen-turbo   # 指定更快/便宜的模型

原理：
    Claude Code 用 DeepSeek V4-Pro 生成 → 本脚本调通义千问审查
    不同厂商、不同架构、不同训练数据 → 真正的异模审查
"""

import os
import sys
import argparse
from pathlib import Path

# 加载 backend/.env
ENV_FILE = Path(__file__).resolve().parent.parent / "backend" / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = value.strip()

import httpx
from openai import OpenAI

REVIEW_PROMPT = """你是独立的审查者（通义千问），你的任务是审查另一款 AI（DeepSeek）的产出。

## 审查立场

你是独立的、挑剔的 reviewer，不是 builder 的队友：
- 默认假设：这份产出有问题。你的任务是找到它们
- 不是"检查有没有问题"——是"假定有问题，找出证据"
- 对每一处你倾向于放过的——问自己"换一个人来看，他会放过吗？"
- 你对 builder 不熟悉——它的推理路径对你来说是陌生的，你需要重新验证每一步

## 审查维度

逐项扫描，输出差量清单：

### ❌ 错误（必须修）
- 事实错误：数据、逻辑、引用有误
- 代码 bug：语法错误、逻辑漏洞、边界条件遗漏
- 推理错误：因果关系搞反、前提不成立、结论推不出来

### 🟡 遗漏（应该补）
- 这个任务有哪些该有的输出/步骤/case，这里没有？
- 有没有隐含假设没有显式写出来？

### 🔶 偏差（方向问题）
- 目标理解跑偏了吗？有没有做偏了？
- 有没有方向和用户意图不一致的地方？

### ⚪ 过度（可以删）
- 有没有用户没要求的功能/内容？
- 有没有过度设计、不必要的复杂度？

### ✏️ 风格（语气/格式）
- 语气/措辞/格式有没有不符合要求的地方？

## 硬规

每条差量必须指向具体位置。指不出具体位置的差量不算。
- ✅ "第 3 段第 2 句……事实错误"
- ✅ "handleTimeout 函数没有处理 timeout=0 的边界"
- ❌ "整体感觉逻辑不够清晰"
- ❌ "表述可以更精炼"

不影响功能的发现不报（绿色差量）。
- 同义表述替换 → 不报
- 同样逻辑换写法 → 不报
- 不影响结果的风格偏好 → 不报

## 待审查内容

{content}

## 请输出差量清单

按【错误→遗漏→偏差→过度→风格】顺序。指不出具体位置的就跳过不写。"""


def get_client() -> OpenAI:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key or api_key == "your-api-key-here":
        print("[cross-review] ERROR: LLM_API_KEY 未配置。请在 backend/.env 中填入通义千问 API Key。", file=sys.stderr)
        sys.exit(1)
    base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    # 通义千问国内直连，不走代理
    http_client = httpx.Client(trust_env=False)
    return OpenAI(api_key=api_key, base_url=base_url, timeout=120.0, http_client=http_client)


def review(content: str, model: str = None) -> str:
    client = get_client()
    model = model or os.getenv("LLM_MODEL", "qwen-plus")

    prompt = REVIEW_PROMPT.format(content=content)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # 低温度，减少幻觉
    )

    return response.choices[0].message.content or ""


def main():
    parser = argparse.ArgumentParser(
        description="异模审查 — 通义千问审查 DeepSeek 产出",
        epilog="示例: python cross_review.py output.md --model qwen-turbo",
    )
    parser.add_argument("file", nargs="?", help="要审查的文件路径")
    parser.add_argument("--stdin", action="store_true", help="从标准输入读取内容")
    parser.add_argument("--model", default=None, help="审查模型（默认 qwen-plus）")
    parser.add_argument("--save", default=None, help="审查结果保存到文件")

    args = parser.parse_args()

    # 读取内容
    if args.stdin:
        content = sys.stdin.read()
    elif args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"[cross-review] ERROR: 文件不存在: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        print("[cross-review] ERROR: 请指定文件路径或使用 --stdin", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if not content.strip():
        print("[cross-review] ERROR: 内容为空，无法审查", file=sys.stderr)
        sys.exit(1)

    model = args.model or os.getenv("LLM_MODEL", "qwen-plus")
    print(f"[cross-review] 审查模型: {model}", file=sys.stderr)
    print(f"[cross-review] 内容长度: {len(content)} 字符", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    try:
        result = review(content, model)
        print(result)

        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"\n[cross-review] 审查结果已保存到: {args.save}", file=sys.stderr)

    except Exception as e:
        print(f"[cross-review] ERROR: 审查失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
