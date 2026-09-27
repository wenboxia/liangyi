#!/usr/bin/env python3
"""
把 capture_demo.mjs 录下的逐帧截图合成 README 用的 demo.gif，并导出决定卡截图。

    python3 docs/visualizations/build_demo_gif.py <capture 目录>
<capture 目录> 里要有 frames/、frames.json、stills/（capture_demo.mjs 的输出）。
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/images"
CAP = Path(sys.argv[1])
W = 820
FONT = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 22)

log = json.loads((CAP / "frames.json").read_text())
real = log[-1]["time"]                      # 页面自己计的耗时，如 6:34
m, s = real.split(":")
caption = f"线上实跑录屏 · hitl 档 · 实际 {int(m)} 分 {int(s)} 秒，压缩播放"

frames, durs = [], []
prev_mode = None
for i, x in enumerate(log):
    im = Image.open(CAP / x["f"]).convert("RGB").resize((W, W), Image.LANCZOS)
    canvas = Image.new("RGB", (W, W + 44), "#141413")
    canvas.paste(im, (0, 44))
    d = ImageDraw.Draw(canvas)
    d.text((16, 9), caption, fill="#FAF9F5", font=FONT)
    tag = {"idle": "", "running": "", "awaiting": "★ 停下等你决定", "done": ""}.get(x["state"], "")
    if tag:
        d.text((W - 16 - d.textlength(tag, font=FONT), 9), tag, fill="#D97757", font=FONT)
    last_of_mode = i + 1 == len(log) or log[i + 1]["mode"] != x["mode"]
    if x["state"] == "idle":
        dur = 600
    elif x["mode"] == "decide":
        dur = 2600 if prev_mode != "decide" else 90   # 停点第一帧停留，后续重复帧快速带过
    elif x["mode"] == "result":
        dur = 4000 if last_of_mode else 400
    else:
        dur = 100
    prev_mode = x["mode"]
    frames.append(canvas.quantize(colors=96, method=Image.MEDIANCUT, dither=Image.NONE))
    durs.append(dur)

OUT.mkdir(parents=True, exist_ok=True)
frames[0].save(OUT / "demo.gif", save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)
print("demo.gif", round((OUT / "demo.gif").stat().st_size / 1e6, 2), "MB,", len(frames), "frames,", sum(durs) / 1000, "s")

card = Image.open(CAP / "stills/decide-2C-rollback.png").convert("RGB")
card.thumbnail((1440, 1440), Image.LANCZOS)
card.save(OUT / "decision-card.png", optimize=True)
print("decision-card.png", card.size)
