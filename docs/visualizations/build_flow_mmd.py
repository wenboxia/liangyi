#!/usr/bin/env python3
"""
生成两张纵向状态机图（mermaid）：auto 档、hitl 档。主体共用，只在 hitl 那份
插入两个决策节点——所以两张图 90% 相同，改一处两边同步。
输出：docs/flow-auto.mmd、docs/flow-hitl.mmd，并写进 README.md（上下叠）和
web/index.html（左右并排）。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

STYLES = """  classDef anchor fill:#F0EEE6,stroke:#B0AEA5,color:#141413
  classDef divA fill:#E4ECF2,stroke:#8FA3B3,color:#141413
  classDef divB fill:#E8F0E6,stroke:#8FB08F,color:#141413
  classDef hitl fill:#FBEFE9,stroke:#D97757,stroke-width:2px,color:#141413
  classDef route fill:#FFF4D6,stroke:#C9A227,color:#141413
  classDef exitA fill:#F8DADA,stroke:#B04141,color:#141413
  classDef exitB fill:#DCEEF3,stroke:#3E7A8C,color:#141413
  classDef done fill:#141413,stroke:#141413,color:#FAF9F5"""

HEAD = """  SEED([原初想法]) --> P0[P0 忠实精炼<br/>anchor]
  P0 --> P10[P1.0 生成对抗角色<br/>anchor · 假对立检测]
  P10 -. 假对立 → 重生成 ≤1 次 .-> P10
  P10 --> P1A[P1A 专家 A<br/>anchor]
  P10 --> P1B[P1B 专家 B<br/>divergent_a · 与 A 互不可见]
  P1A --> P14[P1.4 融合 → v1<br/>anchor 执笔]
  P1B --> P14
  P14 --> P2A[P2A 投资人批判<br/>anchor · 新窗口] --> AF[2A-fix → v2<br/>执笔]
  AF --> P2B[P2B 零上下文单盲<br/>divergent_b · 只见正文] --> BF[2B-fix → v3<br/>执笔]
  BF --> P2C[P2C 知情复审<br/>anchor · 对照 v1/v3 查漂移]"""

AUTO_MID = """  P2C --> CR[2C-rollback → v4<br/>执笔按诊断自判回退]
  CR --> P2D[P2D 拆台<br/>divergent_a · 只攻前提] --> DF[2D-fix → v5<br/>执笔分级判定]
  DF --> R1"""

HITL_MID = """  P2C --> CR[2C-rollback → v4<br/>执笔]
  CR --> H1{{★ HITL ① 停下等你<br/>诊断 + 「当初要 X → 现在变成 Y」}}
  H1 -- 接受 --> P2D
  H1 -- 指定回退 / 指定保留 --> CR2[2C-rollback 带指令重跑一次 → v4<br/>执笔] --> P2D
  P2D[P2D 拆台<br/>divergent_a · 只攻前提] --> DF[2D-fix → v5<br/>执笔分级判定]
  DF --> H2{{★ HITL ② 停下等你<br/>分级表 + 判定}}
  H2 -- 按判定走 --> R1
  H2 -- 按我的指令改 --> DF2[2D-fix 带指令重跑一次 → v5<br/>执笔] --> R1
  H2 -- ★ 前提确实错了<br/>第 1 轮 → 出口 A；第 2 轮 → 以判定书收场 --> EA"""

TAIL = """  R1{致命论据 ≥ 2？<br/>K 级 × 具体性高}
  R1 -- 否 --> V5[产出 v5]
  R1 -- 是 · 第 1 轮 --> EA[出口 A · 回 P1<br/>整链重跑]
  R1 -- 是 · 第 2 轮 --> FORCE[终止条件兜底<br/>强制产出 v5] --> V5
  V5 --> R2{K 占比 ≥ 60%<br/>且第 1 轮？}
  R2 -- 是 --> EB[出口 B · 回 P2<br/>v5 当新初稿]
  R2 -- 否 --> END([结束])
  EA -. 第 2 轮 · 窗口全新开 .-> P0
  EB -. 第 2 轮 · 重跑批判链 .-> P2A
  class P0,P10,P1A,P14,P2A,AF,BF,P2C,CR,DF anchor
  class P1B,P2D divA
  class P2B divB
  class R1,R2 route
  class EA exitA
  class EB exitB
  class END,V5 done"""

auto = "\n".join(["flowchart TB", STYLES, HEAD, AUTO_MID, TAIL])
hitl = "\n".join(["flowchart TB", STYLES, HEAD, HITL_MID, TAIL, "  class H1,H2 hitl\n  class CR2,DF2 anchor"])
(ROOT / "docs/flow-auto.mmd").write_text(auto + "\n", encoding="utf-8")
(ROOT / "docs/flow-hitl.mmd").write_text(hitl + "\n", encoding="utf-8")

# README：两张上下叠
readme = ROOT / "README.md"; s = readme.read_text(encoding="utf-8")
start = "<!-- flow:start -->"; end = "<!-- flow:end -->"
# 两张都放进折叠块：总览由 docs/images/architecture.png 承担，README 首屏不被长图占满
block = (f"{start}\n<details>\n<summary><b>auto 档完整状态机</b>（全自动一次不停）</summary>\n\n```mermaid\n{auto}\n```\n\n</details>\n\n"
         f"<details>\n<summary><b>hitl 档完整状态机</b>（只有 ★ 处不同：两个停点各有三个选项；选第 2 / 3 项那一步带指令重跑一次，2D 选「前提确实错了」走出口 A）</summary>\n\n```mermaid\n{hitl}\n```\n\n</details>\n{end}")
if start in s:
    s = s[:s.index(start)] + block + s[s.index(end) + len(end):]
else:
    old = "![两仪 13 步状态机](web/flow.svg)\n\n图源：`docs/visualizations/build_flow_svg.py`（位置计算生成，改图改脚本）。"
    assert old in s; s = s.replace(old, block + "\n\n图源：`docs/visualizations/build_flow_mmd.py`（两图共用主体，改一处两边同步）。")
readme.write_text(s, encoding="utf-8")

# 网页：两张左右并排
html = ROOT / "web/index.html"; s = html.read_text(encoding="utf-8")
esc = lambda t: t.replace("&", "&amp;")
block = (f'<div class="diagrams"><div class="dcol"><h4>auto 档 · 全自动一次不停</h4><pre class="mermaid">\n{esc(auto)}\n</pre></div>'
         f'<div class="dcol"><h4>hitl 档 · 两个停点等你选</h4><pre class="mermaid">\n{esc(hitl)}\n</pre></div></div>')
a = s.index('<div class="diagrams">'); b = s.index('</pre></div></div>', a) + len('</pre></div></div>')
s = s[:a] + block + s[b:]
html.write_text(s, encoding="utf-8")
print("生成完毕")
