"""Local mock of the Hainan discount-search v2 upstream, for E2E tests only.

默认（E2E 模式）：对任何非空 product_query 都返回一条「标题含查询词 + 12GB+256GB」的候选，
用于验证「后端 → 前端」整条渲染链路，不代表任何真实价格。

MOCK_STRICT=1 时恢复成「只有查询含 S25 才返回」，用于验证匹配失败路径。

真实联调时不要使用本文件；把 .env 里的 HAINAN_API_URL 指向海纳正式地址即可。
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STRICT = os.getenv("MOCK_STRICT", "") == "1"


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        query = str(body.get("product_query") or "").strip()

        rows = []
        if STRICT:
            if "S25" in query:
                rows = [
                    {"title": "三星 Galaxy S25 Ultra 12GB+256GB 钛影黑 5G手机",
                     "price": "6699.00", "direct_link": "https://item.jd.com/1001.html",
                     "mall_name": "京东"},
                    {"title": "三星 Galaxy S25 12GB+256GB 幽蓝 5G手机",
                     "price": "4399.00", "direct_link": "https://item.jd.com/1002.html",
                     "mall_name": "京东"},
                ]
        elif query:
            rows = [{
                "title": "%s 12GB+256GB 全网通 5G手机" % query,
                "price": "4299.00",
                "direct_link": "https://item.jd.com/1000.html",
                "mall_name": "京东",
            }]

        payload = json.dumps({"error_code": 0, "data": {"rows": rows}},
                             ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    port = int(os.getenv("MOCK_PORT", "8899"))
    print("mock upstream on 127.0.0.1:%d (STRICT=%s)" % (port, STRICT))
    ThreadingHTTPServer(("127.0.0.1", port), Mock).serve_forever()
