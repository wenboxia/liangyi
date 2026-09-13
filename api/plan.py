"""GET /api/plan —— 13 步说明。"""
import os, sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 不赌 Vercel 把 api/ 放进 sys.path

from _shared import send_json  # noqa: E402  (api/ 在 sys.path 里，Vercel 以该目录为工作目录)
from chain_api import plan  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        send_json(self, 200, plan())
