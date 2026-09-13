"""
本地开发服务器 —— 标准库，零依赖，`python3 web/server.py` 直接起。

    GET  /              静态站
    GET  /api/plan      13 步说明
    POST /api/step      走一步（见 chain_api.run_one_step）

限次：每个 IP 每天 3 条链。自己用不受限 —— 请求头或 URL 带上 LIANGYI_OWNER_TOKEN
（放在 .env 里，不进仓库）就放行。计数存在内存里，重启清零；部署时换成 KV 即可。
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(HERE.parent / ".env")

from chain_api import plan, run_one_step  # noqa: E402

DAILY_LIMIT = int(os.getenv("LIANGYI_DAILY_LIMIT", "3"))
OWNER_TOKEN = os.getenv("LIANGYI_OWNER_TOKEN", "")
_starts: dict[str, list[float]] = defaultdict(list)     # ip -> 开链时间戳


def _is_owner(handler: BaseHTTPRequestHandler, query: dict) -> bool:
    if not OWNER_TOKEN:
        return False
    tok = handler.headers.get("X-Liangyi-Owner") or (query.get("owner") or [""])[0]
    return tok == OWNER_TOKEN


def _allow_new_chain(ip: str) -> bool:
    now = time.time()
    _starts[ip] = [t for t in _starts[ip] if now - t < 86400]
    if len(_starts[ip]) >= DAILY_LIMIT:
        return False
    _starts[ip].append(now)
    return True


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/plan":
            return self._json(200, plan())
        if u.path in ("/", "/index.html"):
            body = (HERE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        self.send_error(404)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/api/step":
            return self.send_error(404)
        n = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "bad json"})

        files, seed = req.get("files") or {}, (req.get("seed") or "").strip()
        if not files:                                   # 新开一条链才计次
            if not seed or len(seed) < 10:
                return self._json(400, {"error": "想法太短了，至少写一句完整的话。"})
            if len(seed) > 3000:
                return self._json(400, {"error": "想法太长了，3000 字以内。"})
            ip = self.client_address[0]
            if not _is_owner(self, parse_qs(u.query)) and not _allow_new_chain(ip):
                return self._json(429, {"error": f"今天的 {DAILY_LIMIT} 次已用完，明天再来。"})
        try:
            return self._json(200, run_one_step(files, seed))
        except Exception as exc:                         # 让前端看到是哪一步炸了
            return self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, fmt, *args):                  # 安静一点
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8765"))
    print(f"两仪 · 本地服务 http://127.0.0.1:{port}  （限次 {DAILY_LIMIT}/天，"
          f"{'已配置' if OWNER_TOKEN else '未配置'}主人令牌）")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
