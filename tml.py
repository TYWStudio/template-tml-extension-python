#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TML Extension API v1 — Python 宿主 SDK（运行时：python3）。

TYW Launcher 的扩展永远运行在启动器进程之外，只通过 stdin/stdout 的 NDJSON
（每行一个 JSON）交换白名单方法。本文件提供最小实现：
  · 自动完成 initialize 握手；
  · 封装 log / toast / host.info / instances.list / event.subscribe /
    storage.get / storage.set / settings.get / settings.set；
  · 接收宿主广播的事件、优雅退出。

可调用的能力由 manifest.json 的 permissions 决定，未申请的永远不会返回数据。
详见启动器「设置 → 其他 → 拓展」或 https://mtr.tywmc.cn
"""
import sys
import json
import time
import threading

API_VERSION = 1


class TmlError(Exception):
    def __init__(self, code, message):
        self.code = code
        super(TmlError, self).__init__("[%d] %s" % (code, message))


class TmlClient(object):
    def __init__(self):
        self._next_id = 2
        self._lock = threading.Lock()
        self._pending = {}            # id -> [result, error, threading.Event]
        self._event_handlers = []
        self.permissions = []
        self.private_dir = ""
        self.ext_id = ""
        self._ready = False
        self._stop = False

    # ---------- 底层收发 ----------
    def _send(self, obj):
        sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    def _call(self, method, params=None, timeout=5.0):
        with self._lock:
            rid = self._next_id
            self._next_id += 1
            ev = threading.Event()
            self._pending[rid] = [None, None, ev]
        try:
            self._send({"id": rid, "method": method, "params": params or {}})
            if not ev.wait(timeout):
                raise TmlError(-32000, "host timeout: " + method)
            result, error, _ = self._pending[rid]
            if error is not None:
                raise TmlError(error.get("code", -32000), error.get("message", "host error"))
            return result
        finally:
            with self._lock:
                self._pending.pop(rid, None)

    def _loop(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if not isinstance(msg, dict):
                continue
            if "method" in msg:
                method = msg.get("method")
                if method == "initialize":
                    params = msg.get("params") or {}
                    self.ext_id = params.get("extId", "")
                    self.private_dir = params.get("privateDir", "")
                    self.permissions = params.get("permissions", []) or []
                    self._send({"id": msg.get("id"), "result": {"ready": True}})
                    self._ready = True
                    continue
                if method == "shutdown":
                    self._stop = True
                    break
                if method == "event":
                    params = msg.get("params") or {}
                    etype = params.get("type", "")
                    edata = params.get("data", {}) or {}
                    for cb in self._event_handlers:
                        try:
                            cb(etype, edata)
                        except Exception:
                            pass
                    continue
                continue
            # 响应
            if "id" in msg and ("result" in msg or "error" in msg):
                rid = msg.get("id")
                with self._lock:
                    slot = self._pending.get(rid)
                if slot is not None:
                    if "error" in msg:
                        slot[1] = msg["error"]
                    else:
                        slot[0] = msg.get("result")
                    slot[2].set()

    # ---------- 运行入口 ----------
    def run(self, main_fn):
        threading.Thread(target=self._loop, daemon=True).start()
        while not self._ready and not self._stop:
            time.sleep(0.05)
        if not self._ready:
            return
        try:
            main_fn(self)
        finally:
            while not self._stop:
                time.sleep(0.2)

    # ---------- 便捷方法 ----------
    def log(self, message, level="info"):
        self._call("log", {"level": level, "message": message})

    def toast(self, message):
        self._call("toast", {"message": message})

    def host_info(self):
        return self._call("host.info")

    def list_instances(self):
        return self._call("instances.list").get("instances", []) or []

    def subscribe(self, types):
        return self._call("event.subscribe", {"types": types}).get("accepted", []) or []

    def storage_get(self, key):
        return self._call("storage.get", {"key": key}).get("value")

    def storage_set(self, key, value):
        self._call("storage.set", {"key": key, "value": value})

    def settings_get(self, key):
        return self._call("settings.get", {"key": key}).get("value")

    def settings_set(self, key, value):
        self._call("settings.set", {"key": key, "value": value})

    def on_event(self, callback):
        self._event_handlers.append(callback)
