"""
stats_client.py - 在线人数 / 抢票数统计上报模块

对接文档：docs/数据统计接口对接文档.md

设计原则：
1. 所有请求都是"发出去就不管"（fire-and-forget），超时短、异常全部吞掉，
   绝不阻塞或影响抢票主流程；
2. 未配置统计服务地址时，所有函数直接返回，统计功能静默关闭。

使用方式：在下方 DEFAULT_API_BASE 填入服务端地址（打包发布前改一次即可）。
"""

import atexit
import json
import os
import threading
import time
import uuid

import requests

# ================= 配置区域 =================
# 服务端地址，例如 "https://stats.example.com"；留空表示不启用统计功能
DEFAULT_API_BASE = ""

# 接口路径集中在此处，日后服务端更换路径时只改这一行
PATH_ONLINE = "/api/v1/online"
PATH_GRAB = "/api/v1/grab"
PATH_STATS = "/api/v1/stats"

TIMEOUT = 3          # 普通请求超时（秒）
CLOSE_TIMEOUT = 1    # 关闭软件时的上报超时（秒），必须短，避免拖慢退出
RETRY_DELAYS = (1, 3, 5)  # 抢票上报失败后的重试间隔（秒）

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
# ============================================================

_api_base = DEFAULT_API_BASE
_client_id = ""
_is_online = False       # 本进程是否已成功上报"上线"
_loaded = False
_lock = threading.Lock()


# ================== 本地配置读写 ==================
def _read_config():
    """读取本地 config.json，失败返回空字典"""
    try:
        with open(CONFIG_FILE, encoding='utf-8') as f:
            config = json.load(f)
        return config if isinstance(config, dict) else {}
    except Exception:
        return {}


def _write_config_key(key, value):
    """把单个键写回 config.json（合并写入，不影响其它键）"""
    try:
        config = _read_config()
        config[key] = value
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def _ensure_ready():
    """首次调用时从 config.json 加载服务端地址与客户端标识（线程安全）"""
    global _api_base, _client_id, _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        config = _read_config()
        _api_base = (config.get("stats_api_base") or DEFAULT_API_BASE or "").strip()
        _client_id = (config.get("client_id") or "").strip()
        if not _client_id:
            _client_id = uuid.uuid4().hex
            _write_config_key("client_id", _client_id)
        _loaded = True


def get_client_id():
    """获取本机匿名标识（UUID，与账号信息无关），首次调用时生成并持久化"""
    _ensure_ready()
    return _client_id


def get_api_base():
    """获取当前配置的服务端地址，未配置时返回空字符串"""
    _ensure_ready()
    return _api_base


def set_api_base(url):
    """设置服务端地址并持久化到 config.json"""
    global _api_base
    _api_base = (url or "").strip()
    _write_config_key("stats_api_base", _api_base)


def is_enabled():
    """统计功能是否已启用（配置了服务端地址）"""
    return bool(get_api_base())


# ================== HTTP 请求 ==================
def _url(path):
    return _api_base.rstrip('/') + path


def _request(method, path, payload=None, timeout=TIMEOUT):
    """
    发起统计请求，返回响应中的 data 字段；任何异常都返回 None。

    统计接口的失败绝不允许影响抢票主流程，因此这里吞掉所有异常。
    """
    if not _api_base:
        return None
    try:
        if method == 'GET':
            resp = requests.get(_url(path), timeout=timeout)
        else:
            resp = requests.post(_url(path), json=payload, timeout=timeout)
        body = resp.json()
        if isinstance(body, dict) and body.get("code") == 0:
            return body.get("data")
    except Exception:
        pass
    return None


# ================== 对外接口 ==================
def report_online(action="open"):
    """
    上报上线 / 下线，返回当前在线人数（失败或未配置返回 None）。

    action: "open" 打开软件时调用，"close" 关闭软件时调用。
    """
    global _is_online
    _ensure_ready()
    if not _api_base:
        return None

    data = _request('POST', PATH_ONLINE, {"client_id": get_client_id(), "action": action})
    if action == "open":
        if data is not None:
            _is_online = True
    else:
        _is_online = False
    return (data or {}).get("online")


def report_offline():
    """上报下线，使用更短的超时，避免拖慢软件退出"""
    global _is_online
    _ensure_ready()
    if not _api_base:
        return None

    data = _request('POST', PATH_ONLINE, {"client_id": get_client_id(), "action": "close"},
                    timeout=CLOSE_TIMEOUT)
    _is_online = False
    return (data or {}).get("online")


def report_grab(exchange_id):
    """
    抢到票时上报一次（在后台线程执行，不会阻塞抢票）。

    exchange_id: "9" = 2元券，"10" = 4元券，"11" = 6元券
    """
    _ensure_ready()
    if not _api_base:
        return
    threading.Thread(target=_report_grab_sync, args=(str(exchange_id),), daemon=True).start()


def _report_grab_sync(exchange_id):
    """抢票上报的实际执行体：失败后按 RETRY_DELAYS 重试，服务端会做去重"""
    payload = {"client_id": get_client_id(), "exchange_id": exchange_id}
    for delay in (0,) + RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        data = _request('POST', PATH_GRAB, payload)
        if data is not None:
            return data
    return None


def fetch_stats():
    """
    拉取统计数据（只读，不改变任何数据）。

    返回 {"online": int, "total": int, "by_type": {"9": int, "10": int, "11": int}}，
    失败或未配置返回 None。
    """
    _ensure_ready()
    if not _api_base:
        return None
    data = _request('GET', PATH_STATS)
    if not isinstance(data, dict):
        return None
    by_type = data.get("by_type") if isinstance(data.get("by_type"), dict) else {}
    return {
        "online": int(data.get("online") or 0),
        "total": int(data.get("total") or 0),
        "by_type": {k: int(by_type.get(k) or 0) for k in ("9", "10", "11")},
    }


def _on_exit():
    """进程退出兜底：若曾上报上线且未正常下线，补发一次下线请求"""
    if _is_online:
        report_offline()


atexit.register(_on_exit)
