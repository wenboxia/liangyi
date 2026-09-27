"""
两仪论工作流 · 命令行入口

  python -m engine.run --check                          # 预检：硬规则 + API key
  python -m engine.run -s scenarios/xxx.yaml            # 跑一条完整链
  python -m engine.run -s scenarios/xxx.yaml --baseline # 只跑 v0 基线
  python -m engine.run -s scenarios/xxx.yaml -p debug   # 用便宜模型跑通流程
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import REPO_ROOT, check_hard_rules, describe_profile, PROFILES
from .orchestrator import (EXIT_BACK_P1, EXIT_BACK_P2, HardRuleViolation, Orchestrator,
                           Scenario, detect_p1_return)
from .providers import preflight
from .steps import CHAIN

console = Console()


def _rel(path: Path) -> str:
    """安全地显示相对路径。目录在仓库外时退回绝对路径，不该因为打印而崩。"""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def cmd_check(profile: str) -> int:
    console.print(Panel(describe_profile(profile), title="窗口配置", expand=False))

    violations = check_hard_rules(profile)
    if violations:
        for v in violations:
            console.print(f"[red]✗[/red] {v}")
        return 1
    console.print("[green]✓[/green] 方法论硬规则全部通过")
    console.print("    维度 A 可判定 / P2 链条跨维度 / 拆台由 A3 扮演（单盲零上下文由 window.py 在运行时保证）")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Provider")
    table.add_column("状态")
    ok = True
    for name, status in preflight(profile).items():
        good = status == "就绪"
        ok = ok and good
        table.add_row(name, f"[green]{status}[/green]" if good else f"[red]{status}[/red]")
    console.print(table)
    return 0 if ok else 1


def cmd_run(
    scenario_path: Path | None,
    profile: str,
    mode: str,
    baseline_only: bool,
    label: str,
    resume_dir: Path | None = None,
) -> int:
    if resume_dir is not None:
        import json
        meta = json.loads((resume_dir / "run.json").read_text(encoding="utf-8"))
        scenario = Scenario.load(resume_dir / "scenario.yaml")
        profile = meta.get("profile", profile)
        mode = meta.get("mode") or meta.get("hitl") or mode
    else:
        scenario = Scenario.load(scenario_path)

    try:
        orch = Orchestrator(
            scenario, profile=profile, mode=mode, label=label, resume_dir=resume_dir
        )
    except HardRuleViolation as exc:
        console.print(f"[red]{exc}[/red]")
        return 1

    if resume_dir is not None:
        skipped = orch.restore()
        console.print(
            f"[dim]续跑：跳过已完成的 {len(skipped)} 步"
            f"（{', '.join(skipped)}），执笔窗口历史已重建[/dim]\n"
        )

    console.print(Panel(
        f"[bold]{scenario.name}[/bold]\n\n{scenario.seed.strip()[:300]}",
        title=f"场景 · {scenario.id}", expand=False,
    ))
    console.print(orch.describe())
    console.print(f"\n产出目录：{_rel(orch.run_dir)}\n")

    started = time.time()
    try:
        if baseline_only:
            console.print("[dim]v0 基线 · 单 AI 一次性出方案[/dim]")
            orch.run_baseline()
            console.print("[green]✓[/green] idea-v0.md")
        else:
            total = len(CHAIN)
            state = {"before": 0}

            def on_step(step):
                idx = CHAIN.index(step) + 1
                state["before"] = len(orch.trace.steps)
                console.print(
                    f"[dim]{idx:2}/{total}[/dim] [bold]{step.id:12}[/bold] "
                    f"[dim]{step.window:16}[/dim] ", end=""
                )

            def on_step_done(step, content):
                # 跳过的步骤不产生 StepRecord。不加这个判断，trace.steps[-1]
                # 取到的是上一步，于是打出一行「这步花了 $X、想了 N token」的假账。
                if len(orch.trace.steps) == state["before"]:
                    console.print(
                        f"[dim]-[/dim] {step.output:24} [dim]跳过（场景已指定角色）[/dim]"
                    )
                    return
                last = orch.trace.steps[-1]
                flag = ""
                if step.id == "2D-fix" and detect_p1_return(content):
                    flag = " [yellow]判定回 P1[/yellow]" if orch.round == 1 else ""
                console.print(
                    f"[green]✓[/green] {last.output_file:24} "
                    f"[dim]{last.content_chars:>6}字 "
                    f"${last.cost_usd:.4f} {last.duration_ms/1000:.1f}s"
                    f"{' 思考' + str(last.reasoning_tokens) if last.reasoning_tokens else ''}"
                    f"[/dim]{flag}"
                )

            def on_round(n, exit_code, why):
                title = {EXIT_BACK_P1: "回 P1 · 整链重跑", EXIT_BACK_P2: "回 P2 · 重跑批判"}[exit_code]
                console.print(f"\n[bold yellow]第 {n} 轮 · {title}[/bold yellow]  [dim]{why}[/dim]")
                if exit_code == EXIT_BACK_P2:
                    console.print("[dim]P0 / P1 产物沿用上一轮，上一轮的 v5 作为本轮 v1[/dim]")

            orch.run_chain(on_step=on_step, on_step_done=on_step_done, on_round=on_round)
            console.print(f"\n[bold]收场[/bold]：{orch.exit_reason or '产出 v5'}")
    except KeyboardInterrupt:
        orch.finish(status="interrupted")
        console.print("\n[yellow]已中断[/yellow]，产出保留在运行目录")
        return 130
    except Exception as exc:
        orch.finish(status="failed")
        console.print(f"\n[red]失败：{exc}[/red]")
        return 1

    orch.finish()
    elapsed = time.time() - started
    console.print(f"\n{orch.trace.cost_summary()}")
    console.print(f"耗时 {elapsed/60:.1f} 分钟")
    console.print(f"记录 {_rel(orch.run_dir)}/trace.jsonl")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.run", description="两仪论工作流")
    parser.add_argument("-s", "--scenario", type=Path, help="场景 YAML 路径")
    # 档位列表从 PROFILES 取，不写死 —— 写死过一次，加了 demo 档忘了改这里，
    # 结果是 config 里明明有、命令行却说 invalid choice。
    parser.add_argument("-p", "--profile", default="primary",
                        choices=sorted(PROFILES))
    parser.add_argument("--mode", "--hitl", dest="mode", default="auto",
                        choices=["auto", "hitl"],
                        help="auto 全自动一次不停 / hitl 在 2C 回退与 2D 拆台判定两个必停点停下等人")
    parser.add_argument("--baseline", action="store_true", help="只跑 v0 基线")
    parser.add_argument("--label", default="", help="给运行目录加后缀")
    parser.add_argument("--check", action="store_true", help="只做预检")
    parser.add_argument("--resume", type=Path, metavar="RUN_DIR",
                        help="从中断的运行目录续跑（跳过已完成步骤，重建执笔窗口历史）")
    args = parser.parse_args(argv)

    if args.resume:
        return cmd_run(None, args.profile, args.mode, args.baseline, args.label, args.resume)
    if args.check or not args.scenario:
        return cmd_check(args.profile)
    return cmd_run(args.scenario, args.profile, args.mode, args.baseline, args.label)


if __name__ == "__main__":
    sys.exit(main())
