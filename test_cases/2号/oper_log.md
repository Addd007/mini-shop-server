# 操作日志测试用例

> 责任人：2号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：操作日志搜索、用户列表、详情、删除、清空


| 用例编号        | 接口方法   | 接口路径                        | 测试点    | 用例标题            | 前置条件   | 请求数据                                                             | 预期结果           | 优先级 |
| ----------- | ------ | --------------------------- | ------ | --------------- | ------ | ---------------------------------------------------------------- | -------------- | --- |
| TC-OPER-001 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 按人员/时间/内容搜索操作日志 | 已登录管理员 | `page=1` `size=10` `start` `end` `username=Allen7D` `keyword=测试` | 返回操作日志搜索结果     | P1  |
| TC-OPER-002 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 仅按用户名搜索操作日志     | 已登录管理员 | `page=1` `size=10` `username=Allen7D`                            | 返回对应用户的操作日志    | P1  |
| TC-OPER-003 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 仅按关键字搜索操作日志     | 已登录管理员 | `page=1` `size=10` `keyword=测试`                                  | 返回包含关键字的操作日志   | P1  |
| TC-OPER-004 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 操作日志按时间范围无数据    | 已登录管理员 | `page=1` `size=10` `start` `end`（无数据时间范围）                        | 返回空列表或零条数据     | P2  |
| TC-OPER-005 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 操作日志搜索分页参数边界校验  | 已登录管理员 | `page=0` `size=0`                                                | 返回参数校验失败       | P1  |
| TC-OPER-006 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 操作日志搜索页码超范围查询   | 已登录管理员 | `page=9999` `size=10`                                            | 返回空列表或最后页后的空结果 | P2  |
| TC-OPER-007 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 操作日志搜索未登录访问     | 未登录    | `page=1` `size=10`                                               | 返回未认证错误        | P1  |
| TC-OPER-008 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 操作日志搜索普通用户无权限访问 | 普通用户   | `page=1` `size=10`                                               | 返回权限不足错误       | P1  |
| TC-OPER-009 | GET    | `/cms/log/oper/list/search` | 操作日志搜索 | 操作日志搜索非法时间格式校验  | 已登录管理员 | `page=1` `size=10` `start=2026-13-40` `end=abc`                  | 返回参数校验失败       | P1  |
| TC-OPER-010 | GET    | `/cms/log/oper/user/list`   | 用户列表日志 | 查询操作日志中的用户列表成功  | 已登录管理员 | `page=1` `size=10`                                               | 返回用户列表日志       | P1  |
| TC-OPER-011 | GET    | `/cms/log/oper/user/list`   | 用户列表日志 | 用户列表日志无数据查询     | 已登录管理员 | `page=1` `size=10`                                               | 返回空列表或零条数据     | P2  |
| TC-OPER-012 | GET    | `/cms/log/oper/user/list`   | 用户列表日志 | 用户列表日志分页参数边界校验  | 已登录管理员 | `page=0` `size=0`                                                | 返回参数校验失败       | P1  |
| TC-OPER-013 | GET    | `/cms/log/oper/user/list`   | 用户列表日志 | 用户列表日志未登录访问     | 未登录    | `page=1` `size=10`                                               | 返回未认证错误        | P1  |
| TC-OPER-014 | GET    | `/cms/log/oper/user/list`   | 用户列表日志 | 用户列表日志普通用户无权限访问 | 普通用户   | `page=1` `size=10`                                               | 返回权限不足错误       | P1  |
| TC-OPER-015 | GET    | `/cms/log/oper/{id}`        | 操作日志详情 | 查询单条操作日志成功      | 已登录管理员 | `id=1`                                                           | 返回操作日志详情       | P1  |
| TC-OPER-016 | GET    | `/cms/log/oper/{id}`        | 操作日志详情 | 查询单条操作日志不存在失败   | 已登录管理员 | `id=9999`                                                        | 返回记录不存在提示      | P1  |
| TC-OPER-017 | GET    | `/cms/log/oper/{id}`        | 操作日志详情 | 查询单条操作日志非法ID失败  | 已登录管理员 | `id=abc` / `id=0`                                                | 返回参数校验失败       | P1  |
| TC-OPER-018 | GET    | `/cms/log/oper/{id}`        | 操作日志详情 | 未登录查询单条操作日志失败   | 未登录    | `id=1`                                                           | 返回未认证错误        | P1  |
| TC-OPER-019 | GET    | `/cms/log/oper/{id}`        | 操作日志详情 | 无权限查询单条操作日志失败   | 普通用户   | `id=1`                                                           | 返回权限不足错误       | P1  |
| TC-OPER-020 | DELETE | `/cms/log/oper/{id}`        | 删除日志   | 删除操作日志成功        | 已登录管理员 | `id=1`                                                           | 删除成功           | P2  |
| TC-OPER-021 | DELETE | `/cms/log/oper/{id}`        | 删除日志   | 删除不存在的操作日志失败    | 已登录管理员 | `id=9999`                                                        | 返回记录不存在提示      | P1  |
| TC-OPER-022 | DELETE | `/cms/log/oper/{id}`        | 删除日志   | 删除操作日志非法ID失败    | 已登录管理员 | `id=abc` / `id=0`                                                | 返回参数校验失败       | P1  |
| TC-OPER-023 | DELETE | `/cms/log/oper/{id}`        | 删除日志   | 未登录删除操作日志失败     | 未登录    | `id=1`                                                           | 返回未认证错误        | P1  |
| TC-OPER-024 | DELETE | `/cms/log/oper/{id}`        | 删除日志   | 无权限删除操作日志失败     | 普通用户   | `id=1`                                                           | 返回权限不足错误       | P1  |
| TC-OPER-025 | DELETE | `/cms/log/oper/all`         | 清空日志   | 删除所有操作日志成功      | 已登录管理员 | 无                                                                | 清空成功           | P2  |
| TC-OPER-026 | DELETE | `/cms/log/oper/all`         | 清空日志   | 未登录清空操作日志失败     | 未登录    | 无                                                                | 返回未认证错误        | P1  |
| TC-OPER-027 | DELETE | `/cms/log/oper/all`         | 清空日志   | 无权限清空操作日志失败     | 普通用户   | 无                                                                | 返回权限不足错误       | P1  |


## 回归建议

- 核心查询：`TC-OPER-001`、`TC-OPER-010`、`TC-OPER-015`
- 失败场景：`TC-OPER-016`、`TC-OPER-017`、`TC-OPER-018`、`TC-OPER-019`、`TC-OPER-021`、`TC-OPER-022`
- 清理类：`TC-OPER-020`、`TC-OPER-025`、`TC-OPER-026`、`TC-OPER-027`

