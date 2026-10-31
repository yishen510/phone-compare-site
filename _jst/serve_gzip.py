"""本地复现 GitHub Pages 的传输条件：静态文件 + gzip。

为什么不用 python -m http.server：它不压缩，测出来的下载量是 4MB 而不是线上的 645KB，
结论会完全跑偏。这里启动时压一次，之后直接吐压缩体，并带上与线上一致的响应头。

用法：python _jst/serve_gzip.py [端口] [目录]
"""
import gzip
import http.server
import os
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8811
ROOT = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.getcwd()
CACHE = {}


def encoded(path):
    """按 mtime 失效：不然改完文件再测，量到的还是上一次的内容（踩过：A/B 两组其实是同一份）。"""
    key = (path, os.path.getmtime(path), os.path.getsize(path))
    if key not in CACHE:
        with open(path, "rb") as f:
            raw = f.read()
        CACHE.clear()  # 只保留当前这份，避免缓存无限增长
        CACHE[key] = (gzip.compress(raw, 6), len(raw))
    return CACHE[key]


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, extra_headers=()):
        self.send_response(code)
        for k, v in extra_headers:
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        rel = self.path.split("?")[0].lstrip("/") or "index.html"
        path = os.path.abspath(os.path.join(ROOT, rel))
        if not path.startswith(ROOT) or not os.path.isfile(path):
            self.send_error(404)
            return
        body, raw_len = encoded(path)
        # 与 GitHub Pages 对齐：ETag + max-age=600，命中缓存时回 304（回访场景才测得准）
        etag = '"%x-%x"' % (raw_len, int(os.path.getmtime(path)))
        if self.headers.get("If-None-Match") == etag:
            self._send(304, [("ETag", etag), ("Cache-Control", "max-age=600")])
            return
        ctype = "text/html; charset=utf-8" if path.endswith(".html") else "application/octet-stream"
        self._send(200, [
            ("Content-Type", ctype),
            ("Content-Encoding", "gzip"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "max-age=600"),
            ("ETag", etag),
            ("Vary", "Accept-Encoding"),
        ])
        self.wfile.write(body)

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"serving {ROOT} on http://127.0.0.1:{PORT}/ (gzip)", flush=True)
    httpd.serve_forever()
