#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TML 拓展示例（Python）。

演示：握手后打印宿主信息、订阅事件、读取/写入私有存储与设置。
把本文件作为 manifest.json 中 entry 指向的入口即可。
"""
import json
import sys

sys.path.insert(0, ".")
from tml import TmlClient, TmlError


def main(tml):
    tml.log("拓展示例已启动 (python3)", level="info")

    try:
        info = tml.host_info()
        tml.log("宿主信息: " + json.dumps(info, ensure_ascii=False))
    except TmlError as e:
        tml.log("获取宿主信息失败: " + str(e), level="warn")

    accepted = tml.subscribe(["launcher.started", "game.launched", "settings.changed"])
    tml.log("已订阅事件: " + json.dumps(accepted, ensure_ascii=False))
    tml.toast("你好，我是 TML 拓展示例！")

    def on_event(event_type, data):
        tml.log("收到事件 %s: %s" % (event_type, json.dumps(data, ensure_ascii=False)))

    tml.on_event(on_event)

    # 私有存储示例：累计触发次数
    count = tml.storage_get("launch_count") or 0
    try:
        count = int(count)
    except Exception:
        count = 0
    count += 1
    tml.storage_set("launch_count", count)
    tml.log("历史触发次数: " + str(count))

    # 设置示例（命名空间强制为 ext.<id>.*）
    tml.settings_set("ext.%s.greeting" % tml.ext_id, "hello")
    greeting = tml.settings_get("ext.%s.greeting" % tml.ext_id)
    tml.log("读取设置: " + str(greeting))


if __name__ == "__main__":
    TmlClient().run(main)
