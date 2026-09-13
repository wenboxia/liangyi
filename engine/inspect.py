"""
两仪论工作流 · 运行结果查看

  python -m engine.inspect runs/20260829-230613-dev-diagnose      # 摘要
  python -m engine.inspect runs/... --step P2D                    # 某一步的详情
  python -m engine.inspect runs/... --reasoning                   # 所有步骤的推理过程
  python -m engine.inspect runs/... --diff idea-v1.md idea-v5.md  # 版本对比

这是 Phase D 可视化看板的数据层预演 —— 同一份 trace.jsonl，先用命令行读通，
再谈渲染成图。
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .trace import load_trace

console = Console()


def show_summary(run_dir: Path) -> None:
    meta, records = load_trace(run_dir)
    steps = [r for r in records if r.get("kind") == "step"]
    decisions = [r for r in records if r.get("kind") == "decision"]

    header = [
        f"[bold]{meta.get('scenario_name', '?')}[/bold]  ({meta.get('scenario_id')})",
        f"配置 {meta.get('profile')} · HITL {meta.get('hitl')} · 状态 {meta.get('status', '进行中')}",
    ]
    if meta.get("total_cost_usd") is not None:
        header.append(
            f"共 {meta.get('steps')} 步 · ${meta['total_cost_usd']:.4f} · "
            f"输入 {meta.get('tokens_in', 0):,} / 输出 {meta.get('tokens_out', 0):,} tokens · "
            f"{meta.get('reasoning_captured', 0)} 步抓到推理过程"
        )
    console.print(Panel("\n".join(header), expand=False))

    table = Table(show_header=True, header_style="bold")
    for col in ("步骤", "窗口", "坐标", "产出", "字数", "思考", "耗时", "花费"):
        table.add_column(col, justify="right" if col in ("字数", "思考", "耗时", "花费") else "left")

    for r in steps:
        table.add_row(
            r["step_id"], r["window"], r["coordinate"], r["output_file"],
            f"{r['content_chars']:,}",
            str(r["reasoning_tokens"]) if r["reasoning_tokens"] else "—",
            f"{r['duration_ms']/1000:.0f}s",
            f"${r['cost_usd']:.4f}",
        )
    console.print(table)

    if decisions:
        console.print("\n[bold]人工决策点[/bold]")
        for d in decisions:
            mark = "●" if d["triggered"] else "○"
            console.print(
                f"  {mark} {d['step_id']:12} {d['position']:14} {d['mode']}"
                + (f"  [dim]{d['trigger_reason']}[/dim]" if d.get("trigger_reason") else "")
            )
        console.print("[dim]  ○ = 自动通过（本次未触发人工介入）[/dim]")


def show_step(run_dir: Path, step_id: str) -> None:
    meta, records = load_trace(run_dir)
    matches = [r for r in records if r.get("step_id") == step_id and r.get("kind") == "step"]
    if not matches:
        console.print(f"[red]没找到步骤 {step_id}[/red]")
        return
    r = matches[0]

    console.print(Panel(
        f"[bold]{r['step_id']}[/bold] · {r['window']} · {r['model']} ({r['coordinate']})\n"
        f"{r['role']}\n\n"
        f"读取 {', '.join(r['inputs'])} → 写出 {r['output_file']}\n"
        f"{r['content_chars']:,} 字 · ${r['cost_usd']:.4f} · {r['duration_ms']/1000:.1f}s",
        title="步骤信息", expand=False,
    ))

    if r.get("reasoning"):
        console.print(Panel(
            r["reasoning"][:3000] + ("\n…（截断）" if len(r["reasoning"]) > 3000 else ""),
            title=f"推理过程（{r['reasoning_tokens']} tokens）", border_style="dim",
        ))

    out = _artifact(run_dir, r["output_file"], r.get("round"))
    if out.exists():
        text = out.read_text(encoding="utf-8")
        console.print(Panel(
            text[:2500] + ("\n…（截断，完整内容见文件）" if len(text) > 2500 else ""),
            title=r["output_file"],
        ))


def show_reasoning(run_dir: Path) -> None:
    """
    把所有步骤的推理过程列出来。

    这是手动跑方法论时拿不到的东西 —— 只能看到最终输出，看不到模型在想什么。
    有了它，「这个批判 agent 是真在批判还是在敷衍」从推断变成可以直接检验。
    """
    meta, records = load_trace(run_dir)
    for r in records:
        if r.get("kind") != "step" or not r.get("reasoning"):
            continue
        console.print(Panel(
            r["reasoning"][:1500] + ("…" if len(r["reasoning"]) > 1500 else ""),
            title=f"{r['step_id']} · {r['model']} · {r['reasoning_tokens']} tokens",
            border_style="dim", expand=False,
        ))


def _artifact(run_dir: Path, name: str, round_no: int | None = None) -> Path:
    """
    找产物。兼容两种布局：加 loop 之前是 artifacts/xxx，之后是 artifacts/round-N/xxx。

    不做这层兼容的后果不是报错，是**静默给出错数据** —— 第二轮跑完之后
    直接读 artifacts/idea-v5.md 会拿到第一轮的文件，配上第二轮的 trace，
    输出看起来完全正常。这类不一致比崩溃危险得多。
    """
    art = run_dir / "artifacts"
    if round_no is not None:
        return art / f"round-{round_no}" / name
    flat = art / name
    if flat.exists():
        return flat                       # 老布局
    rounds = sorted(art.glob("round-*"), key=lambda d: int(d.name.split("-")[1]))
    for d in reversed(rounds):            # 新布局：默认取最后一轮
        if (d / name).exists():
            return d / name
    return flat


def show_diff(run_dir: Path, a: str, b: str) -> None:
    ta = _artifact(run_dir, a).read_text(encoding="utf-8").splitlines()
    tb = _artifact(run_dir, b).read_text(encoding="utf-8").splitlines()
    console.print(f"[bold]{a}[/bold] ({len(ta)} 行) → [bold]{b}[/bold] ({len(tb)} 行)\n")
    shown = 0
    for line in difflib.unified_diff(ta, tb, fromfile=a, tofile=b, lineterm="", n=1):
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            console.print(f"[green]{line[:200]}[/green]")
        elif line.startswith("-"):
            console.print(f"[red]{line[:200]}[/red]")
        elif line.startswith("@@"):
            console.print(f"[dim]{line}[/dim]")
        shown += 1
        if shown > 160:
            console.print("[dim]…（截断）[/dim]")
            break


def compare_runs(dirs: list[Path]) -> None:
    """
    跨运行对比 —— 同一个场景在不同配置下跑出来的差异。

    Phase E 的消融对照全靠它：同 seed 不同 profile、同 profile 不同 HITL 档位，
    都是这个形状的比较。
    """
    loaded = [(d, *load_trace(d)) for d in dirs]

    table = Table(show_header=True, header_style="bold", title="运行对比")
    table.add_column("步骤")
    for d, meta, _ in loaded:
        table.add_column(f"{meta.get('profile')}\n[dim]{d.name[-18:]}[/dim]", justify="right")

    step_ids: list[str] = []
    for _, _, records in loaded:
        for r in records:
            if r.get("kind") == "step" and r["step_id"] not in step_ids:
                step_ids.append(r["step_id"])

    for sid in step_ids:
        row = [sid]
        for _, _, records in loaded:
            hit = next(
                (r for r in records if r.get("kind") == "step" and r["step_id"] == sid), None
            )
            row.append(
                f"{hit['content_chars']:,}字 ${hit['cost_usd']:.3f}" if hit else "[dim]—[/dim]"
            )
        table.add_row(*row)

    totals = ["[bold]合计[/bold]"]
    for _, meta, records in loaded:
        steps = [r for r in records if r.get("kind") == "step"]
        cost = sum(r["cost_usd"] for r in steps)
        think = sum(r["reasoning_tokens"] for r in steps)
        totals.append(f"[bold]${cost:.3f}[/bold]\n[dim]思考{think:,}[/dim]")
    table.add_row(*totals)
    console.print(table)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="engine.inspect", description="查看运行结果")
    p.add_argument("run_dir", type=Path)
    p.add_argument("--step", help="看某一步的详情（含推理过程）")
    p.add_argument("--reasoning", action="store_true", help="列出所有推理过程")
    p.add_argument("--diff", nargs=2, metavar=("A", "B"), help="对比两个版本")
    p.add_argument("--vs", type=Path, nargs="+", help="与其他运行目录对比")
    args = p.parse_args(argv)

    if not args.run_dir.exists():
        console.print(f"[red]目录不存在：{args.run_dir}[/red]")
        return 1

    if args.vs:
        compare_runs([args.run_dir, *args.vs])
    elif args.step:
        show_step(args.run_dir, args.step)
    elif args.reasoning:
        show_reasoning(args.run_dir)
    elif args.diff:
        show_diff(args.run_dir, *args.diff)
    else:
        show_summary(args.run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
