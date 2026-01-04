# 工程说明：Bilibili 用户主页 → 视频 → 评论区爬取与入库

## 1. 目标与范围
- 使用已登录账号，从用户主页或首页推荐流开始抓取视频列表。
- 逐视频进入详情页，采集视频元信息与完整评论区（主评论 + 回复）。
- 将数据按规范写入数据库，支持长期运行与页面变动。

## 2. 分层架构（强制）
| 层级 | 职责 | 禁止事项 |
| --- | --- | --- |
| Fetcher | 页面请求、登录态维护 | 不解析 DOM/JSON，不做交互 |
| Parser | HTML/JSON 解析，幂等且无状态 | 不进行点击/滚动，不写库 |
| Interaction | 点击、滚动、展开、接口触发等交互行为 | 不解析数据，不写库 |
| Normalizer | 数据清洗、时间/文本标准化 | 不发请求、不交互 |
| Writer | 数据写入数据库（批量或流式） | 不解析、不交互 |
| Orchestrator | 调度全流程，调用各层 | 不跨层绕行调用 |

> **强制**：禁止跨层调用；解析层不允许出现交互逻辑或写库逻辑；交互层只负责行为，不关心解析细节。

## 3. 总体流程
1. 登录账号（Fetcher 负责态管理）。
2. 访问用户主页，解析视频列表。
3. 对去重后的视频逐一：
   - 获取视频页面。
   - 解析视频元信息。
   - 初始化评论区。
   - 循环加载评论（交互可插拔）。
   - 去重并写入数据库。
4. 下一个视频。

> **强制执行顺序**：1) 抓取视频列表 → 2) 视频去重（video_id） → 3) 进入视频页 → 4) 初始化评论区 → 5) 循环加载评论 → 6) 评论去重（comment_id） → 7) 写库 → 8) 下一个视频。

## 4. 起始页面与视频列表解析
- 根节点：`<div class="bili-video-card__wrap">`
- 必备字段：
  | 字段 | 提取方式 |
  | --- | --- |
  | video_id | 从 `<a href="https://www.bilibili.com/video/BVxxxx">` 提取 BV 号 |
  | video_url | 同上 |
  | title | `<h3 class="bili-video-card__info--tit" title>` |
  | author_id | `<a href="//space.bilibili.com/{uid}">` |
  | author_name | `.bili-video-card__info--author` |
  | publish_date | `.bili-video-card__info--date` |
  | view_count | `.bili-video-card__stats--text` |
  | comment_count | `.bili-video-card__stats--text` |
  | duration | `.bili-video-card__stats__duration` |
  | first_seen_at | 抓取时间 |
  | last_seen_at | 抓取时间 |

## 5. 视频页面补充字段
- 入口：`https://www.bilibili.com/video/{video_id}`
- 尽可能提取精确发布时间与实际评论数。

## 6. 评论区抓取与模型
### 6.1 节点
- 主评论节点：`<bili-comment-renderer>`
- 回复节点：`<bili-comment-reply-renderer>`

### 6.2 主评论字段
| 字段 | 来源 |
| --- | --- |
| comment_id | 页面或接口 |
| video_id | 当前视频 |
| user_id | `data-user-profile-id` |
| user_level | 用户等级图标 |
| comment_text | `<p id="contents">`（仅取纯文本） |
| publish_time | `#pubdate` |
| is_reply | `false` |
| parent_comment_id | `null` |

### 6.3 回复评论字段
| 字段 | 来源 |
| --- | --- |
| comment_id | 页面或接口 |
| video_id | 当前视频 |
| user_id | `data-user-profile-id` |
| comment_text | `<p id="contents">`（仅取纯文本） |
| publish_time | `#pubdate` |
| is_reply | `true` |
| parent_comment_id | 主评论 ID |

### 6.4 文本与时间标准化
- 仅提取纯文本，忽略 `<img>`、SVG、装饰节点；保留标点与重复符号。
- 时间标准化：
  - 绝对时间直接解析。
  - 相对时间（如“1小时前”）按抓取时间回推。
  - 统一为 ISO 时间戳。

## 7. 评论加载交互（可扩展）
抽象接口示例：
```python
class CommentInteraction:
    def has_more(self) -> bool:
        ...

    def load_more(self) -> None:
        ...
```
- 支持点击“展开更多评论”、滚动加载或接口拉取等实现方式。
- 典型流程：
  ```
  初始化评论区
  while has_more_comments:
      Interaction.load_more()
      Fetch 当前页面
      Parse 新评论
      去重并写入
  ```

## 8. 数据标准与入库
### 8.1 视频表示例
```json
{
  "video_id": "BVxxxx",
  "title": "...",
  "author_id": "46377861",
  "publish_date": "2025-12-18",
  "view_count": 29000,
  "comment_count": 80,
  "first_seen_at": "...",
  "last_seen_at": "..."
}
```

### 8.2 评论事件表示例
```json
{
  "comment_id": "...",
  "video_id": "BVxxxx",
  "user_id": "hash_xxx",
  "comment_text": "...",
  "publish_time": "...",
  "is_reply": false,
  "parent_comment_id": null,
  "user_level": 5
}
```

## 9. 禁止事项
- 解析层直接调用点击/滚动。
- 使用 `sleep` 代替加载判断。
- 硬编码 DOM 路径（应使用稳健定位）。
- 解析层写数据库。

## 10. 验收标准
- 稳定抓取视频列表与 BV 号。
- 完整抓取主评论与回复。
- 评论加载逻辑可替换，数据结构可直接用于后续分析。

