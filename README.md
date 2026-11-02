# tvbox-cms-source

自用 TVBox / 影视仓 / FongMi 影视等 App 的 CMS 采集源订阅，每日自动同步上游 [krypth/tvbox-cms-source](https://github.com/krypth/tvbox-cms-source)。

## 订阅地址（填入 App 的配置/订阅地址）

| 优先级 | 地址 |
|---|---|
| 1 | `https://gh-proxy.com/https://raw.githubusercontent.com/InkiChang/tvbox-cms-source/main/source.json` |
| 2 | `https://testingcf.jsdelivr.net/gh/InkiChang/tvbox-cms-source@main/source.json` |
| 3 | `https://gcore.jsdelivr.net/gh/InkiChang/tvbox-cms-source@main/source.json` |
| 4 | `https://raw.githubusercontent.com/InkiChang/tvbox-cms-source/main/source.json`（需代理） |

## 源列表

`source.json` 内含 type 1 CMS 采集站（api.php/provide/vod 格式），无需 spider，直接可用。
具体站点以文件内 `sites` 数组为准。

## 自动同步说明

- `.github/workflows/sync-upstream.yml` 每日北京时间 01:30 拉取上游 `source.json`，有变更则自动提交推送。
- **如需手动增删源**：先删除或禁用该 workflow（否则手工修改会被上游覆盖），再编辑 `source.json` 提交即可；jsDelivr 缓存约 12~24 小时，gh-proxy 近实时。

## 声明

本仓库仅为配置索引，不存储任何视频内容；所有站点均为第三方公开 CMS API。
