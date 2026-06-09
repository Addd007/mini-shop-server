# 通知与文章测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：通知列表、公告、文章列表、文章详情、创建更新删除

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| TC-NOTICE-001 | GET | `/cms/notice/list` | 通知列表 | 查询通知列表成功 | 已登录管理员 | `page=1` `size=10` | 返回通知/公告分页列表 | P1 |
| TC-NOTICE-002 | GET | `/cms/notice/{id}` | 通知详情 | 查询通知详情成功 | 已登录 | `id=1` | 返回通知详情 | P1 |
| TC-NOTICE-003 | POST | `/cms/notice` | 通知新增 | 新建通知成功 | 已登录管理员 | `title=测试通知` `content=测试内容` `type=1` | 创建成功 | P1 |
| TC-NOTICE-004 | PUT | `/cms/notice/{id}` | 通知更新 | 更新通知成功 | 已登录管理员 | `id=1` + 更新字段 | 更新成功 | P1 |
| TC-NOTICE-005 | DELETE | `/cms/notice/{ids}` | 通知删除 | 批量删除通知成功 | 已登录管理员 | `ids=[1,2]` | 删除成功 | P2 |
| TC-ARTICLE-001 | GET | `/cms/article/list` | 文章列表 | 查询文章列表成功 | 已登录或公开访问 | `type=1` `page=1` `size=10` | 返回文章分页列表 | P1 |
| TC-ARTICLE-002 | GET | `/cms/article/latest` | 最新文章 | 查询最新文章列表成功 | 已登录或公开访问 | `type=1` `page=1` `size=10` | 返回最新文章列表 | P1 |
| TC-ARTICLE-003 | GET | `/cms/article/{id}` | 文章详情 | 查询文章成功 | 已登录或公开访问 | `id=1` | 返回文章详情 | P1 |
| TC-ARTICLE-004 | POST | `/cms/article` | 新建文章 | 新建文章成功 | 已登录管理员 | `title=测试文章` `summary=摘要` `content=正文` `type=1` | 创建成功 | P1 |
| TC-ARTICLE-005 | PUT | `/cms/article/{id}` | 文章更新 | 更新文章成功 | 已登录管理员 | `id=1` + 更新字段 | 更新成功 | P1 |
| TC-ARTICLE-006 | DELETE | `/cms/article/{id}` | 文章删除 | 删除文章成功 | 已登录管理员 | `id=1` | 删除成功 | P2 |

## 回归建议

- 内容链路：`TC-NOTICE-001`、`TC-NOTICE-002`、`TC-ARTICLE-001`、`TC-ARTICLE-002`、`TC-ARTICLE-003`
- 管理链路：`TC-NOTICE-003`、`TC-NOTICE-004`、`TC-NOTICE-005`、`TC-ARTICLE-004`、`TC-ARTICLE-005`、`TC-ARTICLE-006`
