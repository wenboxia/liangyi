"""
两仪 · 在线入口的后端核心

一次调用 = 链条走一步。运行目录里的所有文件（scenario.yaml / run.json /
trace.jsonl / decision-log.md / artifacts/round-1/*）以一个 {相对路径: 内容}
的字典在客户端和服务端之间来回传，**服务端不保存任何状态**。

为什么这么做而不是一个请求跑完：完整链在演示档也要八到十分钟，
serverless 单函数装不下；分步之后每一步最长一两分钟，任何平台都能跑。

为什么不另写一套链条逻辑：提示词、模型路由、窗口隔离、判定解析全在引擎里，
另写一套等于再养一份会漂的副本。这里只做「把文件铺进临时目录 → 让引擎续跑一步
→ 把目录读回来」，引擎一行不改。restore() 本来就能从产物重建窗口历史。
"""
from __future__ import annotations

import dataclasses
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.orchestrator import IDEA_SEPARATOR, Orchestrator, Scenario  # noqa: E402
from engine.steps import CHAIN  # noqa: E402

PROFILE = "demo"
ROUND_DIR = "artifacts/round-1"

# 给前端看的每一步说明。措辞与 engine/PIPELINE.md 一致。
STEP_INFO = {
    "P0":          ("忠实精炼", "把原始想法精炼一遍。不改逻辑、不扩展、不质疑——先让它可以被对抗"),
    "P1.0":        ("生成对抗角色", "生成两个结构性对立的专家角色，并检测是不是假对立"),
    "P1A":         ("专家 A 出方案", "专家 A 视角独立出一份方案"),
    "P1B":         ("专家 B 出方案", "专家 B 独立出方案，这个窗口看不到 A 的方案"),
    "P1.4":        ("融合成 v1", "执笔窗口把两份方案融合成单一立场的第一版"),
    "P2A":         ("投资人批判", "怀疑论投资人视角：市场与商业逻辑哪里站不住"),
    "2A-fix":      ("改出 v2", "执笔窗口按批判修改，逐条记下采纳还是驳回"),
    "P2B":         ("零上下文单盲复审", "只拿到方案正文、不给任何背景的陌生读者"),
    "2B-fix":      ("改出 v3", "按单盲意见修改"),
    "P2C":         ("知情复审", "对照 v1 与 v3，查产品身份有没有被悄悄换掉"),
    "2C-rollback": ("回退漂移，改出 v4", "把跑偏的部分退回去"),
    "P2D":         ("拆台专家", "只攻方案赖以成立的前提，不挑细节"),
    "2D-fix":      ("分级判定，改出 v5", "给每条拆台论据分级，判框架内改还是回 P1 重做"),
}


def _write_files(run_dir: Path, files: dict[str, str]) -> None:
    (run_dir / ROUND_DIR).mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        p = run_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _read_files(run_dir: Path) -> dict[str, str]:
    out = {}
    for p in run_dir.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(run_dir))] = p.read_text(encoding="utf-8")
    return out


def _record_dict(rec) -> dict:
    d = dataclasses.asdict(rec)
    d.pop("reasoning", None)          # 推理链太长，前端用不上
    return d


def plan() -> list[dict]:
    """13 步的静态说明，前端先把列表画出来再逐步点亮。"""
    return [{"id": s.id, "phase": s.phase, "window": s.window,
             "title": STEP_INFO[s.id][0], "desc": STEP_INFO[s.id][1],
             "output": s.output}
            for s in CHAIN]


PENDING = "artifacts/round-1/_pending.json"   # hitl 必停点等人时，这一步的产出暂存在这


def _awaiting_payload(orch, step, raw: str) -> dict:
    """必停点交回浏览器时附带的上下文：选项、诊断/分级表、材料包。措辞与终端一致。"""
    from engine import interact, advisor, digest
    pos = step.decision_point
    options = [{"key": k, "name": n, "desc": d} for k, n, d in interact.OPTIONS.get(pos, [])]
    context, shift = "", None
    if pos == "2C-rollback":
        context = orch.read_artifact("P2C-review.md") if orch.has_artifact("P2C-review.md") else ""
        try:                                        # 「你当初要 X，现在变成 Y」—— 一次便宜的摘要调用
            v1, v3 = orch.read_artifact("idea-v1.md"), orch.read_artifact("idea-v3.md")
            d = digest.version_diff(v1, v3)
            shift = d.change if d.ok else None
        except Exception:
            shift = None
    elif pos == "2D-fix":
        context = raw.split(IDEA_SEPARATOR)[0] if IDEA_SEPARATOR in raw else raw
    try:
        brief = advisor.build_brief(orch, pos, interact.OPTIONS.get(pos, []))
    except Exception:
        brief = ""
    return {"position": pos, "step_id": step.id, "title": STEP_INFO[step.id][0],
            "options": options, "context": context, "shift": shift, "brief": brief}


def run_one_step(files: dict[str, str], seed: str, mode: str = "auto",
                 decision: dict | None = None) -> dict:
    """
    走一步。files 为空表示新开一条链。

    mode      —— auto / hitl，**开链时定死**，之后从 run.json 里读，请求里再传也不改
    decision  —— hitl 在必停点等人时，浏览器把决定带回来：{position, choice, instruction}

    返回 {files, event, done, verdict, next, awaiting}：
      files    —— 走完这一步之后运行目录里的全部文件，原样传回来即可续走
      event    —— 这一步的 trace 记录 + 产物内容 + 这一步写的决策日志片段
      awaiting —— hitl 到必停点了：这一步的产出已暂存，等人选；带选项、上下文、材料包
      done     —— 13 步走完了没有
      verdict  —— 走完之后的判定（produced-v5 / back-to-p1）
    """
    from engine.orchestrator import AwaitingDecision, BackToP1
    from engine.providers import Completion
    from engine.interact import Decision

    tmp = Path(tempfile.mkdtemp(prefix="liangyi-web-"))
    try:
        _write_files(tmp, files)
        sc_path = tmp / "scenario.yaml"
        if sc_path.exists():
            scenario = Scenario.load(sc_path)
            try:
                mode = json.loads((tmp / "run.json").read_text(encoding="utf-8")).get("mode") or mode
            except Exception:
                pass
        else:
            scenario = Scenario(id="web", name="访客的想法", seed=seed.strip())
        mode = "hitl" if mode == "hitl" else "auto"

        # 上一个请求在必停点暂存的产出：带回来就不再调模型
        precomputed = {}
        pend = tmp / PENDING
        if pend.exists():
            j = json.loads(pend.read_text(encoding="utf-8"))
            precomputed[j["step_id"]] = Completion(**j["completion"])
            pend.unlink()

        def provider(step, raw, gate):
            pos = step.decision_point
            if decision and decision.get("position") == pos and decision.get("choice"):
                instr = (decision.get("instruction") or "").strip()
                return Decision(decision["choice"], instruction=instr, rationale=instr)
            raise AwaitingDecision(pos, "", None)      # execute() 会把 raw / completion 填进来

        orch = Orchestrator(scenario, profile=PROFILE, mode=mode, resume_dir=tmp,
                            decision_provider=provider if mode == "hitl" else None,
                            precomputed=precomputed)
        orch.restore()
        todo = orch.pending()
        if not todo:
            exit_code, why = orch._decide_next_round()
            orch.finish()
            meta = json.loads((tmp / "run.json").read_text(encoding="utf-8"))
            return {"files": _read_files(tmp), "event": None, "done": True,
                    "verdict": meta.get("verdict"), "exit": exit_code, "why": why,
                    "total_cost": meta.get("total_cost_usd", 0), "next": None}

        step = todo[0]
        log_before = (tmp / "decision-log.md").read_text(encoding="utf-8") \
            if (tmp / "decision-log.md").exists() else ""
        before = len(orch.trace.steps)

        try:
            orch.execute(step)
        except AwaitingDecision as pending:
            # 产出暂存，交回浏览器等人选。Completion 整包序列化，下一个请求原样塞回。
            pend.parent.mkdir(parents=True, exist_ok=True)
            pend.write_text(json.dumps({
                "step_id": step.id, "raw": pending.raw,
                "completion": dataclasses.asdict(pending.completion),
            }, ensure_ascii=False), encoding="utf-8")
            return {"files": _read_files(tmp), "event": None, "done": False,
                    "verdict": None, "next": step.id,
                    "awaiting": _awaiting_payload(orch, step, pending.raw)}
        except BackToP1 as back:
            # 人判定前提错了。和 auto 档模型自判一样收场：留一份判定书，不产出 v5。
            rec = orch.trace.steps[-1] if len(orch.trace.steps) > before else None
            head = ""
            if step.id in files_pending_raw(files):
                head = files_pending_raw(files)[step.id]
            judgment = (head.split(IDEA_SEPARATOR)[0] if IDEA_SEPARATOR in head else head).strip()
            judgment += f"\n\n## 人工判定\n\n回 P1 重做。{back}\n"
            orch.write_artifact("P2D-fix-judgment.md", judgment)
            orch.finish()
            meta = json.loads((tmp / "run.json").read_text(encoding="utf-8"))
            return {"files": _read_files(tmp), "done": True, "verdict": "back-to-p1", "next": None,
                    "event": {"step_id": step.id, "title": STEP_INFO[step.id][0],
                              "output_file": "P2D-fix-judgment.md", "content": judgment,
                              "decision_log": "", "record": _record_dict(rec) if rec else None,
                              "roles": None, "skipped": False, "human": decision}}

        rec = _record_dict(orch.trace.steps[-1]) if len(orch.trace.steps) > before else None
        out_name = next((n for n in (step.output, "P2D-fix-judgment.md")
                         if orch.has_artifact(n)), step.output)
        content = orch.read_artifact(out_name) if orch.has_artifact(out_name) else ""
        log_after = (tmp / "decision-log.md").read_text(encoding="utf-8") \
            if (tmp / "decision-log.md").exists() else ""
        log_delta = log_after[len(log_before):].strip()

        remaining = orch.pending()
        done = not remaining
        verdict = None
        if done:
            orch.finish()
            verdict = json.loads((tmp / "run.json").read_text(encoding="utf-8")).get("verdict")

        # P1.0 跑完角色就定了 —— 把它带给前端展示「两仪」到底是哪两仪
        roles = None
        if step.id == "P1.0" and orch.scenario.has_roles:
            roles = {"role_a": orch.scenario.role_a, "stance_a": orch.scenario.stance_a,
                     "role_b": orch.scenario.role_b, "stance_b": orch.scenario.stance_b,
                     "tension": orch.scenario.tension}

        return {
            "files": _read_files(tmp),
            "event": {"step_id": step.id, "title": STEP_INFO[step.id][0],
                      "output_file": out_name, "content": content,
                      "decision_log": log_delta, "record": rec, "roles": roles,
                      "skipped": rec is None,
                      "human": decision if (decision and decision.get("position") == step.decision_point) else None},
            "done": done, "verdict": verdict,
            "next": remaining[0].id if remaining else None,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def files_pending_raw(files: dict[str, str]) -> dict[str, str]:
    """从请求带来的 files 里取出暂存的 raw（BackToP1 收场时要用它写判定书）。"""
    try:
        j = json.loads(files.get(PENDING, "") or "{}")
        return {j["step_id"]: j["raw"]} if j else {}
    except Exception:
        return {}
