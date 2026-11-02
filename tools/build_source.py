#!/usr/bin/env python3
"""构建 TVBox CMS 订阅源 source.json（纯标准库，无第三方依赖）。

上游（按优先级）:
  1. ziyuanzu 资源组监测清单 status=ok 的源 — 主上游，自带健康度/评分
  2. krypth/tvbox-cms-source 的 source.json sites
  3. yujian0815/fnmedia-ext 的 providers.py DEFAULT_SOURCES（ast 解析）
  4. zhang-wei-ye/bofangqi 的 lib/source_store.dart kDefaultSources（regex 解析）

去重规则: API 域名相同 或 规范化名称相同（去"资源站/资源/采集站/影视"后缀）
视为同一源，按 ziyuanzu > krypth > fnmedia > bofangqi 优先保留。
任一上游拉取失败则退出码 1 且不写 source.json（保留上一版可用订阅）。
"""
from __future__ import annotations

import ast
import json
import re
import sys
import urllib.request
from datetime import datetime
from urllib.parse import urlparse

ZIYUANZU_URL = "https://mylazily.github.io/ziyuanzhan/data/latest.json"
KRYPTH_URL = "https://raw.githubusercontent.com/krypth/tvbox-cms-source/main/source.json"
FNMEDIA_URL = "https://raw.githubusercontent.com/yujian0815/fnmedia-ext/main/proxy/providers.py"
BOFANGQI_URL = "https://raw.githubusercontent.com/zhang-wei-ye/bofangqi/master/lib/source_store.dart"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) tvbox-source-builder/1.0"}


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def dom(api: str) -> str:
    d = urlparse(api).netloc.lower()
    return d[4:] if d.startswith("www.") else d


def norm_name(name: str) -> str:
    s = (name or "").strip()
    changed = True
    while changed and s:
        changed = False
        for suf in ("资源站", "资源采集站", "采集站", "影视资源站", "资源", "影视"):
            if s.endswith(suf) and len(s) > len(suf):
                s = s[: -len(suf)].strip()
                changed = True
    return s.lower()


def slug(api: str) -> str:
    s = re.sub(r"[^a-z0-9_]", "", dom(api).replace(".", "_").replace("-", "_"))
    return s or "site"


def load_ziyuanzu() -> tuple[list[dict], str]:
    j = json.loads(fetch(ZIYUANZU_URL))
    out = []
    for r in j.get("resources", []):
        api = (r.get("api") or "").strip()
        if r.get("status") != "ok" or not api or "provide/vod" not in api:
            continue
        out.append({
            "origin": "ziyuanzu",
            "name": (r.get("name") or "").strip() or dom(api),
            "api": api,
            "rating": r.get("rating"),
            "todayUpdates": r.get("todayUpdates"),
            "resourceCount": r.get("resource_count"),
        })
    out.sort(key=lambda x: (-(x.get("rating") or 0), -(x.get("todayUpdates") or 0)))
    return out, str(j.get("timestamp", ""))


def load_krypth() -> list[dict]:
    j = json.loads(fetch(KRYPTH_URL))
    out = []
    for s in j.get("sites", []):
        api = (s.get("api") or "").strip()
        if not api:
            continue
        out.append({"origin": "krypth", "name": (s.get("name") or "").strip() or dom(api), "api": api})
    return out


def load_fnmedia() -> list[dict]:
    tree = ast.parse(fetch(FNMEDIA_URL))
    for node in ast.walk(tree):
        target = value = None
        if isinstance(node, ast.Assign):          # X = [...]
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):     # X: list[dict] = [...]
            target, value = node.target, node.value
        if target is not None and getattr(target, "id", "") == "DEFAULT_SOURCES" and value is not None:
            data = ast.literal_eval(value)
            return [
                {"origin": "fnmedia", "name": str(d.get("name", "")).strip() or dom(d["api"]),
                 "api": str(d["api"]).strip()}
                for d in data if d.get("api")
            ]
    raise RuntimeError("DEFAULT_SOURCES not found in fnmedia providers.py")


def load_bofangqi() -> list[dict]:
    src = fetch(BOFANGQI_URL)
    m = re.search(r"kDefaultSources\s*=\s*\[(.*?)\]", src, re.S)
    if not m:
        raise RuntimeError("kDefaultSources not found in bofangqi source_store.dart")
    out = []
    for name, api in re.findall(r"VideoSource\(\s*name:\s*'([^']*)'\s*,\s*api:\s*'([^']*)'", m.group(1)):
        if api:
            out.append({"origin": "bofangqi", "name": name.strip() or dom(api), "api": api.strip()})
    if not out:
        raise RuntimeError("no VideoSource entries parsed from bofangqi")
    return out


def main() -> int:
    z, ts = load_ziyuanzu()
    k = load_krypth()
    f = load_fnmedia()
    b = load_bofangqi()

    if len(z) < 10:
        print(f"[abort] ziyuanzu ok-sources only {len(z)}, upstream data abnormal", file=sys.stderr)
        return 1

    sites: list[dict] = []
    seen_dom: dict[str, str] = {}
    seen_name: dict[str, str] = {}

    def add(items: list[dict]) -> int:
        added = 0
        for it in items:
            d, n = dom(it["api"]), norm_name(it["name"])
            if d in seen_dom or (n and n in seen_name):
                continue
            key = slug(it["api"])
            if any(s["key"] == key for s in sites):
                key = f"{key}_{len(sites)}"
            site = {
                "key": key,
                "name": it["name"],
                "type": 1,
                "api": it["api"],
                "searchable": 1,
                "quickSearch": 1,
            }
            if it.get("rating") is not None:
                site["rating"] = it["rating"]
            sites.append(site)
            seen_dom[d] = key
            if n:
                seen_name[n] = key
            added += 1
        return added

    az, ak, af, ab = add(z), add(k), add(f), add(b)

    doc = {
        "name": "InkiChang 聚合CMS订阅源",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "desc": (
            f"自动聚合构建: ziyuanzu监测清单ok源 {az} 个 + krypth/tvbox-cms-source {ak} 个 "
            f"+ fnmedia-ext {af} 个 + bofangqi {ab} 个，域名/名称去重共 {len(sites)} 源。"
            f"上游监测时间: {ts}。每天自动重建。"
        ),
        "sites": sites,
    }
    with open("source.json", "w", encoding="utf-8", newline="\n") as fp:
        json.dump(doc, fp, ensure_ascii=False, indent=2)
        fp.write("\n")

    print(f"upstream: ziyuanzu_ok={len(z)} krypth={len(k)} fnmedia={len(f)} bofangqi={len(b)} (monitor ts={ts})")
    print(f"merged: ziyuanzu+{az} krypth+{ak} fnmedia+{af} bofangqi+{ab} total={len(sites)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
