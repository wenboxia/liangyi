"""
Vercel 入口 —— 一个 handler 服务三条路由，形状与 web/server.py 完全一致：

    GET  /            静态页（自己读 web/index.html，不依赖平台的静态托管）
    GET  /api/plan    13 步说明
    POST /api/step    链条走一步

Vercel 的 Python 运行时（CLI 59+）要求 pyproject.toml 里指定唯一入口，
不再把 api/ 下每个文件各当一个函数，所以原来的 plan.py / step.py 合到这里。
限次逻辑在 _shared.py：配了 KV 就跨实例计数，没配退回内存计数并在响应头标明。
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import DAILY_LIMIT, ROOT, allow_new_chain, client_ip, is_owner, send_json  # noqa: E402
from chain_api import plan, run_one_step  # noqa: E402

INDEX = ROOT / "web" / "index.html"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/plan":
            return send_json(self, 200, plan())
        if path in ("/", "/index.html"):
            body = INDEX.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        return send_json(self, 404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/api/step":
            return send_json(self, 404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return send_json(self, 400, {"error": "bad json"})

        files, seed = req.get("files") or {}, (req.get("seed") or "").strip()
        limit_kind = ""
        if not files:                                   # 新开一条链才计次
            if not seed or len(seed) < 10:
                return send_json(self, 400, {"error": "想法太短了，至少写一句完整的话。"})
            if len(seed) > 3000:
                return send_json(self, 400, {"error": "想法太长了，3000 字以内。"})
            if not is_owner(self.headers, parse_qs(u.query)):
                ok, limit_kind = allow_new_chain(client_ip(self.headers))
                if not ok:
                    return send_json(self, 429, {"error": f"今天的 {DAILY_LIMIT} 次已用完，明天再来。"})
        try:
            out = run_one_step(files, seed, mode=req.get('mode') or 'auto', decision=req.get('decision'))
        except Exception as exc:                        # 让前端看到是哪一步炸了
            return send_json(self, 500, {"error": f"{type(exc).__name__}: {exc}"})
        return send_json(self, 200, out, {"X-Liangyi-Limit": limit_kind} if limit_kind else None)
