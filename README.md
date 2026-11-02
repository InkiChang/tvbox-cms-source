# tvbox-cms-source

TVBox / 影视仓 / FongMi 等播放器可用的 **CMS 采集源聚合订阅**。`source.json` 由脚本自动聚合构建，不手工维护。

## 订阅地址（地址不变，内容每日自动更新）

| 链路 | 地址 |
|---|---|
| gh-proxy（国内推荐） | `https://gh-proxy.com/https://raw.githubusercontent.com/InkiChang/tvbox-cms-source/main/source.json` |
| jsDelivr | `https://testingcf.jsdelivr.net/gh/InkiChang/tvbox-cms-source@main/source.json` |
| jsDelivr (gcore) | `https://gcore.jsdelivr.net/gh/InkiChang/tvbox-cms-source@main/source.json` |
| GitHub raw | `https://raw.githubusercontent.com/InkiChang/tvbox-cms-source/main/source.json` |

## 聚合上游（按优先级）

1. **ziyuanzu 资源组监测清单**（主上游）：`https://mylazily.github.io/ziyuanzhan/data/latest.json`
   只取 `status=ok` 的源，按评分/今日更新量降序排列，自带健康度剔除（宕机自动出榜、恢复自动回榜）。
2. **krypth/tvbox-cms-source**：手工筛选的稳定 CMS 源。
3. **yujian0815/fnmedia-ext**：飞牛影视扩展内置的 `DEFAULT_SOURCES`。
4. **zhang-wei-ye/bofangqi**：Flutter 播放器预置的 `kDefaultSources`（2026-10 实测筛选）。

去重规则：API 域名相同 **或** 规范化名称相同（去「资源站/资源/采集站/影视」等后缀）视为同一源，优先保留 ziyuanzu 版本。仅保留苹果 CMS V10 标准接口（`provide/vod`）。

## 自动构建

- 每天北京时间 **01:30**（GitHub Actions cron）运行 `tools/build_source.py` 重建 `source.json`，有变化才提交
- 支持手动触发：Actions → Build CMS Subscription → Run workflow
- 任一上游拉取失败则放弃本次构建，保留上一版可用订阅
- 部分源含成人内容（ziyuanzu 清单原样保留），介意请自行筛选使用

## 手工维护

不需要也不建议直接编辑 `source.json`（会被下次构建覆盖）。想增删源请改 `tools/build_source.py` 里的上游列表与过滤规则。

## 声明

本仓库仅为配置索引，不存储任何视频内容；所有站点均为第三方公开 CMS API，使用行为及后果由使用者自行承担，请遵守当地法律法规。
