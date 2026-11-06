# Emby for Kodi Next Gen · core 分支

上游 [Emby for Kodi Next Gen](https://github.com/MediaBrowser/plugin.video.emby) 的精简定制分支。职责边界明确：Emby 承担媒体管理与元数据刮削，Kodi 仅负责本地媒体库播放。

本分支以官方 12.5.1 为上游基线，合入 narapeka 的 12.5.1.1 精简改动，并在评分同步、同步稳定性与发布流程上做定制。

| 项目 | 说明 |
|---|---|
| 当前版本 | 12.5.3 |
| 上游基线 | 12.5.1（`next-gen-dev-python3`） |
| 版本体系 | 12.5.2 起为本分支独立编号，不跟随上游 |
| 发布渠道 | [Releases](https://github.com/wabisabi926/plugin.video.emby/releases) |
| 许可 | GNU GPL v3 |

## 1. 功能裁剪

### 1.1 移除模块

| 模块 | 处理方式 |
|---|---|
| 动态浏览与搜索 | 移除服务端动态浏览与搜索；同步节点、播放、播放列表、下一集、收藏等入口保留 |
| 同步播放与远程投放 | 移除 SyncPlay、Watch Together、Remote Play |
| 直播、PVR 与录制 | 移除相关代码及上下文菜单项 |
| 照片与相册 | 删除 `core/photo.py`、`core/photoalbum.py` |
| 离线下载 | 移除下载与离线内容管理 |
| 主题媒体 | 移除本地主题音乐、视频的上传与下载任务（`hooks/themes.py`） |
| 影院预告 | 删除 `core/trailer.py`，Kodi 的 trailer 字段保持为空 |
| 转码 | 不再请求服务端转码 |
| 备份与去重 | 删除 `helper/backup.py`、`helper/deduplicate.py` |

上下文菜单同步收缩，仅保留多版本、刷新条目与设置三项；录制、特辑、跳转、相似推荐、下载、投放、随机播放等条目移除。

### 1.2 规模对比

| 指标 | 上游 12.5.1 | 本分支 |
|---|---|---|
| 设置项 | 241 | 38 |
| `settings.xml` | 2486 行 | 342 行 |
| 语言包 | 55 | 2（`en_gb`、`zh_cn`） |
| Python 文件 | 68 | 64 |
| 资源文件 | — | 减少 31 个 |

上游的 `README.md`、`CONTRIBUTING.md`、应用截图、banner 与图标素材已移除；原 README 由本文档替代。

## 2. 相对上游的实现差异

### 2.1 播放

- 采用 Emby 静态 HTTP 流并跟随原始 HTTP(S) 媒体 URL，保留 ISO、蓝光、DVD 直读路径。
- 版本组未变更时原位更新，保留 Kodi 电影/文件 ID、默认版本与本地流信息。
- 播放源按名称排序，`[Default]` 优先；手动选择版本以所选条目为准，并记忆剧集的上次选择（`helper/versions.py`）。
- 剧集自动沿用下一集版本，支持同季记忆与跨季切换；支持该接口的 Kodi fork 可在起播前选版。
- 字幕遵循 Kodi 当前语言与可见性设置，无匹配时恢复原选择。
- 精简片头/片尾跳过提示，修正续播倒计时单位换算；设置提供清理图片缓存与压缩数据库。

### 2.2 同步

- 启动同步最多建立四路持久连接，顺序处理，使用 UTC 检查点。
- 分页统一：默认 100 条；单集、歌曲、音乐艺术家 1000 条（`helper/paging.py`，不读取 Kodi 设置）。
- 单个媒体库失败不影响其他库；失败时保留检查点供下次重试；关机或异常时回滚检查点。
- Emby 未返回媒体类型时，仍可更新已看状态、续播与收藏；连接断开后重连 WebSocket。

### 2.3 元数据

- 电影与剧集默认使用 TMDb ID，单集优先 TMDb，缺失时回退 TVDb。
- 封面与章节图按需加载，尺寸与质量档内置（`helper/artwork.py`）。
- 简化封面、演员与工作室的同步逻辑。

### 2.4 接口

- 剧集选版：`/api/v1/episodes/versions|resolve|media/...`，供支持该接口的 Kodi fork 在起播前选版；无效地址或来源返回 404。
- Similar：`/api/v1/items/similar?type=movie|tvshow&dbid=<Kodi ID>&limit=<1-100>`，仅返回已同步条目的 ID 与媒体库名。
- 服务仅监听 `127.0.0.1:57342`，供同机 Kodi 调用；接口版本需与客户端一致。

## 3. 分支特性

### 3.1 评分同步

Emby 仅暴露单一 `CommunityRating`，不含来源信息。本分支将其拆分为可独立配置的评分项：

| 配置项 | 数据来源 | 写入目标 |
|---|---|---|
| 社区评分来源 | `CommunityRating` | `rating` 表，类型由配置决定 |
| 影评人评分 | `CriticRating` | `tomatometerallcritics`，除以 10 归一化 |
| 豆瓣评分 | `ProviderIds.DoubanRating` | `douban` |
| 音乐评分 | 专辑/歌曲 `CommunityRating` | `album.fRating`、`song.rating` |

配置语义：

- 社区评分来源可选 TMDb / IMDb / 豆瓣 / 未知来源 / 不同步。
- 「不同步」仅跳过社区评分，不影响豆瓣与影评人评分。
- 豆瓣评分默认关闭，其余配置项默认开启。

数据来源说明：

- 豆瓣分可由 StrmAssistant（神医助手）等插件覆盖 `CommunityRating` 写入，亦可写入 `ProviderIds.DoubanRating`。
- 两种来源并存时优先采用 `ProviderIds.DoubanRating` 的数值。

写入策略：

- 构建 Kodi uniqueid 时跳过 `*Rating` 类 ProviderId，避免豆瓣分被识别为外部 ID。
- 关闭某项评分后停止写入；已有评分在条目下次刷新时移除。
- 更新时仅清理受管的 6 种评分类型，不影响其他来源的评分数据。

### 3.2 稳定性修复

- 收藏子内容同步：修复多内容 ID 解析越界，服务器或映射缺失时安全跳过。
- 启动同步按库隔离，单个库异常不阻断整体流程；关机或异常时回滚检查点，锁等待上限 5 秒。
- 单集 uniqueid 优先 TMDb，缺失时回退 TVDb。
- 多版本参数传递：改用 `sys.listitem` 获取路径并做 URL 编码，改用 `sendall` 发送，socket 关闭前判空。

### 3.3 构建与发布

- GitHub Actions 在 `core` 分支 `addon.xml` 版本号变更时自动打包并创建 Release。
- tag 格式 `插件ID-分支-版本`，产物为 `插件ID-版本.zip`。
- 发布说明自动抽取 `changelog.txt` 中对应版本段落。
- 打包排除 `__pycache__`、`*.pyc`、`*.pyo`、`.DS_Store`、`Thumbs.db`。

## 4. 版本管理

版本号定义于 `addon.xml` 的 `version` 属性；`changelog.txt` 以 `x<版本号>` 作为段落起始标记：

```
x12.5.3
==========
评分开关
- ...
```

CI 比对本次提交与上次提交的版本号：版本变更且同名 Release 不存在时发布，否则跳过。仅修改代码而不变更版本号不会触发发布。

## 5. 安装

1. 从 [Releases](https://github.com/wabisabi926/plugin.video.emby/releases) 下载 zip 包。
2. Kodi → 设置 → 插件 → 从 zip 文件安装。
3. 在插件配置中填写 Emby 服务器地址与账号，选择需同步的媒体库。

从官方 12.5.1 切换到此定制版时使用全新安装并重新同步媒体库；在定制版内升级剧集选版和 Similar 接口无需重新同步。

## 6. 上游合并

上游仓库 `MediaBrowser/plugin.video.emby`，开发分支 `next-gen-dev-python3`。

```bash
git fetch origin
git log --oneline core..origin/next-gen-dev-python3
git diff --stat core...origin/next-gen-dev-python3
```

本分支删除大量上游文件，直接 merge 会恢复已移除的功能，建议按文件 cherry-pick。

## 7. 已知限制

- 仅提供中英文界面，其余语言回退至英文。
- 不支持服务端动态浏览与搜索；Kodi 中缺失的媒体需先完成同步。指向 `mode=browse`、`mode=search` 的第三方路径将返回空列表。
- 评分开关仅控制媒体库写入；插件内部为播放构造的列表项仍使用 Emby 实时数据。
- 关闭评分后不会立即清空既有数据，需条目自身刷新一次。

## 8. 许可与第三方依赖

本项目为 Emby for Kodi Next Gen（作者 quickmic）的衍生作品，遵循 GNU GPL v3，见 `LICENSE.txt`。修改与再分发须遵守同一许可。

豆瓣数据依赖 Emby 端的 StrmAssistant（神医助手）等刮削插件，本项目不包含亦不分发。
