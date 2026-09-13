"""
Vercel Python 函数共用的一小块：路径、限次、JSON 响应。

Vercel 把 api/ 下每个 .py 当一个函数；下划线开头的文件不会被当成路由，
所以共用逻辑放这里。真正的链条逻辑在 web/chain_api.py，引擎一行不改。

限次：每 IP 每天 3 条链。serverless 实例之间不共享内存，所以**内存计数在线上
基本不起作用**（换个实例或冷启动就归零）。配了 Upstash / Vercel KV 的
REST 变量（KV_REST_API_URL + KV_REST_API_TOKEN）就用 KV 计数，跨实例有效；
没配就退回内存计数，并在响应头里标 X-Liangyi-Limit: memory 让人知道这是弱的。
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "web"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

DAILY_LIMIT = int(os.getenv("LIANGYI_DAILY_LIMIT", "3"))
OWNER_TOKEN = os.getenv("LIANGYI_OWNER_TOKEN", "")
# Upstash 集成注入的变量名有两套，哪套在就用哪套
KV_URL = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL") or ""
KV_TOKEN = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN") or ""

_mem: dict[str, list[float]] = defaultdict(list)


def client_ip(headers) -> str:
    fwd = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For") or ""
    return fwd.split(",")[0].strip() or "unknown"


def is_owner(headers, query: dict) -> bool:
    if not OWNER_TOKEN:
        return False
    tok = headers.get("x-liangyi-owner") or headers.get("X-Liangyi-Owner") or (query.get("owner") or [""])[0]
    return tok == OWNER_TOKEN


def _kv(cmd: list) -> object:
    req = urllib.request.Request(
        KV_URL, data=json.dumps(cmd).encode(), method="POST",
        headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read()).get("result")


def allow_new_chain(ip: str) -> tuple[bool, str]:
    """返回 (放不放行, 用的是哪种计数)。"""
    if KV_URL and KV_TOKEN:
        day = time.strftime("%Y%m%d", time.gmtime())
        key = f"liangyi:starts:{day}:{ip}"
        try:
            n = int(_kv(["INCR", key]))
            if n == 1:
                _kv(["EXPIRE", key, 86400])
            return n <= DAILY_LIMIT, "kv"
        except Exception:
            pass                                    # KV 挂了就退回内存，别把入口一起挂掉
    now = time.time()
    _mem[ip] = [t for t in _mem[ip] if now - t < 86400]
    if len(_mem[ip]) >= DAILY_LIMIT:
        return False, "memory"
    _mem[ip].append(now)
    return True, "memory"


def send_json(handler, code: int, obj, extra: dict | None = None) -> None:
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    for k, v in (extra or {}).items():
        handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(body)
