#!/usr/bin/env python3
"""
生成 web/flow.svg —— 两仪 13 步状态机的横向图，README 和网页共用同一个文件。

不用 mermaid 的原因：这张图有三条跨子图的回边，mermaid 一遇到就放弃横向布局，
要么排成 5000px 宽的一行，要么竖成 2700px 高。位置自己算，三行横排、回边走弧线。
配色沿用 anthropic.com 那套（底 #FAF9F5、字 #141413、强调 #D97757）。
"""
from pathlib import Path

W, H = 1600, 810
BG, INK, MUTED, BORDER, ACC = "#FAF9F5", "#141413", "#87867F", "#B0AEA5", "#D97757"
C_ANCHOR, C_DIVA, C_DIVB = "#F0EEE6", "#E4ECF2", "#E8F0E6"
C_ROUTE, C_EXITA, C_EXITB, C_EXITC = "#FFF4D6", "#F8DADA", "#DCEEF3", "#E9E8E4"
BW, BH = 150, 62          # 节点宽高
FONT = "-apple-system, 'PingFang SC', 'Helvetica Neue', Arial, sans-serif"

out = []
w = out.append


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, title, sub, fill, stroke=BORDER, sw=1, tag=None, width=BW):
    title, sub = esc(title), esc(sub)
    w(f'<rect x="{x}" y="{y}" width="{width}" height="{BH}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    w(f'<text x="{x+width/2}" y="{y+25}" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}">{title}</text>')
    w(f'<text x="{x+width/2}" y="{y+45}" text-anchor="middle" font-size="11" fill="{MUTED}">{sub}</text>')
    if tag:
        w(f'<rect x="{x+width-58}" y="{y-11}" width="58" height="20" rx="10" fill="{ACC}"/>')
        w(f'<text x="{x+width-29}" y="{y+3}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#fff">{tag}</text>')


def arrow(x1, y1, x2, y2, dashed=False, color=INK, label=None, curve=None, lx=None, ly=None):
    d = f"M{x1},{y1} " + (f"Q{curve[0]},{curve[1]} {x2},{y2}" if curve else f"L{x2},{y2}")
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    w(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="url(#ah)"/>')
    if label:
        label = esc(label)
        lx = lx if lx is not None else (x1 + x2) / 2
        ly = ly if ly is not None else (y1 + y2) / 2 - 8
        w(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11" fill="{MUTED}">{label}</text>')


def selfloop(x, y, label, width=BW):
    """节点上方一个小环，标"带指令重跑本步"。"""
    cx = x + width / 2
    w(f'<path d="M{cx-22},{y} C{cx-34},{y-34} {cx+34},{y-34} {cx+22},{y}" fill="none" stroke="{ACC}" stroke-width="1.4" stroke-dasharray="5 4" marker-end="url(#ahacc)"/>')
    w(f'<text x="{cx}" y="{y-30}" text-anchor="middle" font-size="10.5" fill="{ACC}">{label}</text>')


w(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">')
w(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
w('<defs>'
  f'<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>'
  f'<marker id="ahacc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{ACC}"/></marker>'
  '</defs>')

X0 = 76

# ---------- 行标题 ----------
def rowlabel(y, text):
    w(f'<text x="{X0}" y="{y}" font-size="12" font-weight="700" fill="{MUTED}" letter-spacing="1">{text}</text>')

# ---------- 第一行：P1 ----------
Y1 = 96
rowlabel(Y1 - 10, "P1 · 对抗式方案生成")
box(X0, Y1, "原初想法", "访客输入", "#fff", width=110)
xs1 = [X0 + 140, X0 + 320, X0 + 500, X0 + 500, X0 + 700]
box(xs1[0], Y1, "P0 忠实精炼", "anchor", C_ANCHOR)
box(xs1[1], Y1, "P1.0 生成对抗角色", "anchor · 假对立检测", C_ANCHOR, width=170)
box(xs1[2], Y1 - 46, "P1A 专家 A", "anchor", C_ANCHOR)
box(xs1[3], Y1 + 46, "P1B 专家 B", "divergent_a · 与 A 互不可见", C_DIVA, width=190)
box(xs1[4] + 40, Y1, "P1.4 融合 → v1", "anchor 执笔", C_ANCHOR)
arrow(X0 + 110, Y1 + BH/2, xs1[0], Y1 + BH/2)
arrow(xs1[0] + BW, Y1 + BH/2, xs1[1], Y1 + BH/2)
arrow(xs1[1] + 170, Y1 + BH/2, xs1[2], Y1 - 46 + BH/2)
arrow(xs1[1] + 170, Y1 + BH/2, xs1[3], Y1 + 46 + BH/2)
arrow(xs1[2] + BW, Y1 - 46 + BH/2, xs1[4] + 40, Y1 + BH/2)
arrow(xs1[3] + 190, Y1 + 46 + BH/2, xs1[4] + 40, Y1 + BH/2)
# P1.0 自环
selfloop(xs1[1], Y1, "假对立 → 重生成 ≤1 次", width=170)

# ---------- 第二行：P2 ----------
Y2 = 300
rowlabel(Y2 - 10, "P2 · 四轮批判链（批判换新窗口，修改同一执笔）")
names = [("P2A 投资人批判", "anchor · 新窗口", C_ANCHOR, None),
         ("2A-fix → v2", "执笔", C_ANCHOR, None),
         ("P2B 零上下文单盲", "divergent_b · 只见正文", C_DIVB, None),
         ("2B-fix → v3", "执笔", C_ANCHOR, None),
         ("P2C 知情复审", "anchor · 对照 v1/v3", C_ANCHOR, None),
         ("2C-rollback → v4", "执笔 · 回退漂移", C_ANCHOR, "HITL ①"),
         ("P2D 拆台", "divergent_a · 只攻前提", C_DIVA, None),
         ("2D-fix → v5", "执笔 · 分级判定", C_ANCHOR, "HITL ②")]
xs2 = [X0 + i * 188 for i in range(8)]
for (t, s_, c, tag), x in zip(names, xs2):
    box(x, Y2, t, s_, c, stroke=ACC if tag else BORDER, sw=2 if tag else 1, tag=tag)
for i in range(7):
    arrow(xs2[i] + BW, Y2 + BH/2, xs2[i+1], Y2 + BH/2)
selfloop(xs2[5], Y2, "hitl：指定回退 / 指定保留 → 带指令重跑")
selfloop(xs2[7], Y2, "hitl：框架内改 → 带指令重跑")
# P1.4 → P2A：从第一行末尾折下来
arrow(xs1[4] + 40 + BW/2, Y1 + BH, xs2[0] + BW/2, Y2, curve=(xs1[4] + 40 + BW/2, Y2 - 60), label="v1 进入批判链", lx=xs1[4] + 40 + BW/2 + 70, ly=Y2 - 70)

# ---------- 第三行：判定与出口 ----------
def elbow(pts, dashed=False, color=INK, label=None, lx=None, ly=None, marker=True):
    """正交折线。pts 是拐点列表。"""
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    mk = ' marker-end="url(#ah)"' if (marker and color == INK) else (' marker-end="url(#ahacc2)"' if marker else "")
    w(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash}{mk} stroke-linejoin="round"/>')
    if label:
        w(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11" fill="{MUTED}">{esc(label)}</text>')

Y3 = 520
rowlabel(Y3 - 10, "判定与出口（两轮封顶 · 单链 $3 封顶）")
rx, ry = X0 + 150, Y3 + 31
w(f'<polygon points="{rx},{ry-48} {rx+120},{ry} {rx},{ry+48} {rx-120},{ry}" fill="{C_ROUTE}" stroke="#C9A227" stroke-width="1.4"/>')
w(f'<text x="{rx}" y="{ry-6}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{INK}">致命论据 ≥ 2？</text>')
w(f'<text x="{rx}" y="{ry+12}" text-anchor="middle" font-size="10.5" fill="{MUTED}">K 级 × 具体性高 · hitl 可直接选回 P1</text>')
# 2D-fix → R1：从第二行末尾下来、沿第三行上方走到 R1 顶
midy = Y3 - 50
elbow([(xs2[7] + BW/2, Y2 + BH), (xs2[7] + BW/2, midy), (rx, midy), (rx, ry - 48)], label="分级判定 → 路由", lx=(xs2[7] + BW/2 + rx) / 2, ly=midy - 8)
# R1 否 → V5 → R2 否 → END
bx_v5 = rx + 200
w(f'<rect x="{bx_v5}" y="{Y3}" width="{BW}" height="{BH}" rx="8" fill="{INK}"/>')
w(f'<text x="{bx_v5+BW/2}" y="{Y3+25}" text-anchor="middle" font-size="13" font-weight="700" fill="{BG}">产出 v5</text>')
w(f'<text x="{bx_v5+BW/2}" y="{Y3+45}" text-anchor="middle" font-size="11" fill="#C8C5BC">框架内消化</text>')
arrow(rx + 120, ry, bx_v5, ry, label="否", ly=ry - 8)
r2x = bx_v5 + BW + 180
w(f'<polygon points="{r2x},{ry-46} {r2x+112},{ry} {r2x},{ry+46} {r2x-112},{ry}" fill="{C_ROUTE}" stroke="#C9A227" stroke-width="1.4"/>')
w(f'<text x="{r2x}" y="{ry-4}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{INK}">K 占比 ≥ 60%</text>')
w(f'<text x="{r2x}" y="{ry+13}" text-anchor="middle" font-size="10.5" fill="{MUTED}">且第 1 轮？</text>')
arrow(bx_v5 + BW, ry, r2x - 112, ry)
ex = r2x + 150
w(f'<rect x="{ex}" y="{Y3+8}" width="110" height="46" rx="23" fill="{INK}"/>')
w(f'<text x="{ex+55}" y="{Y3+36}" text-anchor="middle" font-size="13" font-weight="700" fill="{BG}">结束</text>')
arrow(r2x + 112, ry, ex, ry, label="否", ly=ry - 8)

# 出口一行（第四行）：全部竖直/正交落下，不穿主体
Y4 = Y3 + 118
exA_x = rx - 95
box(exA_x, Y4, "出口 A · 回 P1", "整链重跑，只带原初想法", C_EXITA, stroke="#B04141", width=190)
elbow([(rx, ry + 48), (rx, Y4)], label="是 · 第 1 轮", lx=rx + 46, ly=ry + 78)
exC_x = exA_x + 230
box(exC_x, Y4, "出口 C · 结构性死锁", "第 2 轮仍 ≥ 2，议题重叠 ≥ 60%", C_EXITC, stroke="#666", width=230)
elbow([(rx + 60, ry + 24), (rx + 60, ry + 62), (exC_x + 115, ry + 62), (exC_x + 115, Y4)], label="是 · 第 2 轮", lx=exC_x + 30, ly=ry + 58)
fx = exC_x + 270
box(fx, Y4, "终止条件兜底", "第 2 轮，重叠 < 60% → 强制产出 v5", "#fff", width=230)
elbow([(rx + 90, ry + 36), (rx + 90, ry + 74), (fx + 115, ry + 74), (fx + 115, Y4)], label="是 · 第 2 轮", lx=fx - 40, ly=ry + 70)
# 兜底 → 产出 v5（从兜底右侧上去接 v5 底部）
elbow([(fx + 230, Y4 + BH/2), (fx + 250, Y4 + BH/2), (fx + 250, Y3 + BH + 16), (bx_v5 + BW/2, Y3 + BH + 16), (bx_v5 + BW/2, Y3 + BH)])
exB_x = r2x - 95
box(exB_x, Y4, "出口 B · 回 P2", "v5 当新初稿，只重跑批判链", C_EXITB, stroke="#3E7A8C", width=190)
elbow([(r2x, ry + 46), (r2x, Y4)], label="是", lx=r2x + 14, ly=ry + 78)

# ---------- 回边：沿左边距绕回，不穿主体 ----------
w(f'<defs><marker id="ahA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#B04141"/></marker>'
  f'<marker id="ahB" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#3E7A8C"/></marker></defs>')
def ret(pts, color, mk, label, lx, ly, rotate=False):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    w(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6" stroke-dasharray="6 5" stroke-linejoin="round" marker-end="url(#{mk})"/>')
    tr = f' transform="rotate(-90 {lx} {ly})"' if rotate else ""
    w(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11" fill="{color}"{tr}>{esc(label)}</text>')
# 出口 A → P0：左出，沿 x=10 上去，到 P0 顶部上方进
ret([(exA_x, Y4 + BH/2), (30, Y4 + BH/2), (30, Y1 - 58), (xs1[0] + BW/2, Y1 - 58), (xs1[0] + BW/2, Y1)],
    "#B04141", "ahA", "出口 A：新一轮 · 窗口全新开 · 从 P0 重跑", 18, (Y4 + Y1) / 2 + 40, rotate=True)
# 出口 B → P2A：从底部出去，沿 x=6 上到第二行上方，进 P2A 顶
ret([(exB_x + 95, Y4 + BH), (exB_x + 95, Y4 + BH + 22), (52, Y4 + BH + 22), (52, Y2 - 44), (xs2[0] + BW/2, Y2 - 44), (xs2[0] + BW/2, Y2)],
    "#3E7A8C", "ahB", "出口 B：新一轮 · 只重跑 P2 批判链", 63, (Y4 + Y2) / 2 + 60, rotate=True)

# ---------- 图例 ----------
LY = H - 30
items = [(C_ANCHOR, BORDER, "anchor：执笔 / 专家 A / 投资人 / 知情复审"), (C_DIVA, BORDER, "divergent_a：专家 B / 拆台"),
         (C_DIVB, BORDER, "divergent_b：单盲"), ("#FBEFE9", ACC, "HITL 停点：auto 自动通过，hitl 停下等你")]
lx = 24
for fill, stroke, text in items:
    w(f'<rect x="{lx}" y="{LY}" width="16" height="16" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="{2 if stroke==ACC else 1}"/>')
    w(f'<text x="{lx+22}" y="{LY+13}" font-size="11.5" fill="{INK}">{text}</text>')
    lx += 22 + len(text) * 11.5 * 0.92 + 26
w(f'<text x="{lx}" y="{LY+13}" font-size="11.5" fill="{MUTED}">虚线 = 回边 · 两个档位走同一张图</text>')
w('</svg>')

Path("web/flow.svg").write_text("\n".join(out), encoding="utf-8")
print("写出 web/flow.svg", len("\n".join(out)), "字节")
