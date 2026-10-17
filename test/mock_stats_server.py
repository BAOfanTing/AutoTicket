"""
mock_stats_server.py - 本地模拟统计服务端（仅用于开发预览）

用法：
    1. python test/mock_stats_server.py   # 启动模拟服务端（默认自动选可用端口）
    2. 在 config.json 中加入 "stats_api_base": "http://127.0.0.1:<端口>"
    3. 重启 gui.py，即可看到"实时统计"面板

注意：本文件仅供本地开发/演示使用，数据存在内存里，进程结束即丢失。
正式对接请使用 docs/数据统计接口对接文档.md 中的服务端实现。
"""

import json
import sys
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VALID_IDS = {"9", "10", "11"}
# 候选端口：Windows 的 Hyper-V/WSL 会预留一些端口段，逐个尝试直到绑定成功
CANDIDATE_PORTS = [8877, 9090, 4200, 7500, 8899]

online_users = {}   # client_id -> last_seen
grab_records = []   # (client_id, exchange_id, created_at)


def build_stats():
    """组装统计数据：在线人数 + 总票数 + 各券种票数"""
    by_type = {"9": 0, "10": 0, "11": 0}
    for _, ex_id, _ in grab_records:
        by_type[ex_id] += 1
    return {"online": len(online_users), "total": len(grab_records), "by_type": by_type}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # 静默默认的访问日志
        pass

    def _reply(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(length) or b"{}")

        if self.path == "/api/v1/online":
            client_id, action = req.get("client_id"), req.get("action")
            if not client_id or action not in ("open", "close"):
                return self._reply({"code": 400, "msg": "invalid params", "data": None})
            if action == "open":
                # 兜底：清掉 24 小时没动静的会话（模拟正式服务端行为）
                cutoff = datetime.now() - timedelta(hours=24)
                for cid in [c for c, t in online_users.items() if t < cutoff]:
                    del online_users[cid]
                online_users[client_id] = datetime.now()
            else:
                online_users.pop(client_id, None)
            print(f"[{datetime.now():%H:%M:%S}] {action:5s} {client_id[:8]}  在线人数: {len(online_users)}")
            return self._reply({"code": 0, "msg": "ok", "data": {"online": len(online_users)}})

        if self.path == "/api/v1/grab":
            client_id, ex_id = req.get("client_id"), str(req.get("exchange_id"))
            if not client_id or ex_id not in VALID_IDS:
                return self._reply({"code": 400, "msg": "invalid params", "data": None})
            dup = any(c == client_id and e == ex_id and t > datetime.now() - timedelta(seconds=60)
                      for c, e, t in grab_records)
            if not dup:
                grab_records.append((client_id, ex_id, datetime.now()))
            stats = build_stats()
            print(f"[{datetime.now():%H:%M:%S}] 抢到 {ex_id} 号券  总票数: {stats['total']}")
            return self._reply({"code": 0, "msg": "ok",
                                "data": {"total": stats["total"], "by_type": stats["by_type"]}})

        self._reply({"code": 404, "msg": "not found", "data": None})

    def do_GET(self):
        if self.path.startswith("/api/v1/stats"):
            return self._reply({"code": 0, "msg": "ok", "data": build_stats()})
        self._reply({"code": 404, "msg": "not found", "data": None})


if __name__ == "__main__":
    ports = [int(sys.argv[1])] if len(sys.argv) > 1 else CANDIDATE_PORTS

    server = None
    for port in ports:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError as e:
            print(f"端口 {port} 不可用（{e}），尝试下一个...")

    if server is None:
        print("所有候选端口都被占用，请手动指定一个端口，例如：")
        print("    python test/mock_stats_server.py 5000")
        sys.exit(1)

    actual_port = server.server_address[1]
    print(f"模拟统计服务端已启动: http://127.0.0.1:{actual_port}")
    print(f"在 config.json 中加入 \"stats_api_base\": \"http://127.0.0.1:{actual_port}\" 后重启 gui.py 即可预览统计面板")
    print("Ctrl+C 退出\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出")
