#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把扩展打包成 .tmlext（本质是带 manifest.json 的 zip）。

用法：python build.py [输出文件名]
依赖：Python 3 标准库，无需安装第三方包。
"""
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    with open(os.path.join(HERE, "manifest.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)
    ext_id = manifest.get("id", "extension")
    out = sys.argv[1] if len(sys.argv) > 1 else (ext_id + ".tmlext")
    files = ["manifest.json", "main.py", "tml.py"]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in files:
            path = os.path.join(HERE, name)
            if os.path.exists(path):
                z.write(path, name)
    print("已打包: " + out)


if __name__ == "__main__":
    main()
