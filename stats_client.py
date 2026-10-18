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
import re
import threading
import time
import uuid

import requests

# ================= 配置区域 =================
# 服务端地址；留空表示不启用统计功能（config.json 里的 stats_api_base 优先）
DEFAULT_API_BASE = "https://www.relx5th.space"

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


def get_scoped_client_id(account_key=""):
    """按账号生成的客户端标识。

    在线人数按 client_id 去重，同一台机器跑多个账号时如果都用设备级 UUID，
    服务端只会算一个人。这里把「设备标识 + 账号标识」拼起来，
    让每个账号在服务端占独立的一条在线记录。

    account_key: 账号的唯一标识（优先 user_id，其次 login_name）。
                 为空时退回设备级 UUID（未登录状态）。
    """
    _ensure_ready()
    raw = str(account_key or "").strip()
    if not raw:
        return _client_id
    # 只保留服务端 client_id 允许的字符（A-Za-z0-9_-），长度截断到 64
    safe = re.sub(r'[^A-Za-z0-9_-]', '', raw)[:24]
    if not safe:
        return _client_id
    return ("%s-%s" % (_client_id[:32], safe))[:64]


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
def report_online(action="open", account_key=""):
    """
    上报上线 / 下线，返回当前在线人数（失败或未配置返回 None）。

    action: "open" 打开软件时调用，"close" 关闭软件时调用。
    account_key: 账号标识，用于让同一台机器上的多个账号各占一条在线记录。
                 留空则用设备级标识。
    """
    global _is_online
    _ensure_ready()
    if not _api_base:
        return None

    data = _request('POST', PATH_ONLINE,
                    {"client_id": get_scoped_client_id(account_key), "action": action})
    if action == "open":
        if data is not None:
            _is_online = True
    else:
        _is_online = False
    return (data or {}).get("online")


def report_offline(account_key=""):
    """上报下线，使用更短的超时，避免拖慢软件退出"""
    global _is_online
    _ensure_ready()
    if not _api_base:
        return None

    data = _request('POST', PATH_ONLINE,
                    {"client_id": get_scoped_client_id(account_key), "action": "close"},
                    timeout=CLOSE_TIMEOUT)
    _is_online = False
    return (data or {}).get("online")


def report_grab(exchange_id, account_key=""):
    """
    抢到票时上报一次（在后台线程执行，不会阻塞抢票）。

    exchange_id: "9" = 2元券，"10" = 4元券，"11" = 6元券
    account_key: 账号标识，与在线统计保持一致

    每张票都有独立的 request_id，重试时复用同一个，
    所以服务端能精确区分「同一张票重试」和「抢到多张票」。
    """
    _ensure_ready()
    if not _api_base:
        return
    # request_id 在这里生成一次，整次重试链路共用
    request_id = "g-%d-%s" % (int(time.time() * 1000), uuid.uuid4().hex[:16])
    threading.Thread(target=_report_grab_sync,
                     args=(str(exchange_id), account_key, request_id),
                     daemon=True).start()


def _report_grab_sync(exchange_id, account_key="", request_id=None):
    """抢票上报的实际执行体：失败后按 RETRY_DELAYS 重试

    request_id 在整个重试过程中保持不变，服务端据此幂等去重，
    因此「网络抖动导致的重试」不会重复计数。
    """
    payload = {
        "client_id": get_scoped_client_id(account_key),
        "exchange_id": exchange_id,
        "request_id": request_id,
    }
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

    返回 {"online": int, "total": int, "by_type": {...}, "stats_enabled": bool}，
    失败或未配置返回 None。

    stats_enabled 为服务端下发的开关：False 表示服务端已关闭统计功能，
    客户端应隐藏实时统计模块。老版本服务端没有该字段时按 True 处理。
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
        "stats_enabled": data.get("stats_enabled", True) is not False,
    }


def _on_exit():
    """进程退出兜底：若曾上报上线且未正常下线，补发一次下线请求"""
    if _is_online:
        report_offline()


atexit.register(_on_exit)
