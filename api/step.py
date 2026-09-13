"""POST /api/step —— 链条走一步。请求/响应形状与 web/server.py 完全一致。"""
import json
import os, sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 不赌 Vercel 把 api/ 放进 sys.path
from urllib.parse import parse_qs, urlparse

from _shared import DAILY_LIMIT, allow_new_chain, client_ip, is_owner, send_json  # noqa: E402
from chain_api import run_one_step  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        u = urlparse(self.path)
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
            out = run_one_step(files, seed)
        except Exception as exc:                        # 让前端看到是哪一步炸了
            return send_json(self, 500, {"error": f"{type(exc).__name__}: {exc}"})
        return send_json(self, 200, out, {"X-Liangyi-Limit": limit_kind} if limit_kind else None)
