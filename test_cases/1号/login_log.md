# 登录日志测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：登录日志查询、详情、删除、清空


| 用例编号          | 接口方法 | 接口路径                 | 测试点    | 用例标题              | 前置条件   | 请求数据                                           | 预期结果         | 优先级 |
| ------------- | ---- | -------------------- | ------ | ----------------- | ------ | ---------------------------------------------- | ------------ | --- |
| TC-LOGIN-001  | GET  | `/cms/log/login/list` | 登录日志   | 查询登录日志列表成功        | 已登录管理员 | `page=1` `size=10` `start` `end`               | 返回登录日志分页列表   | P1  |
| TC-LOGIN-002  | GET  | `/cms/log/login/list` | 登录日志   | 登录日志列表仅传开始时间查询    | 已登录管理员 | `page=1` `size=10` `start`                     | 返回符合开始时间条件的列表 | P1  |
| TC-LOGIN-003  | GET  | `/cms/log/login/list` | 登录日志   | 登录日志列表仅传结束时间查询    | 已登录管理员 | `page=1` `size=10` `end`                       | 返回符合结束时间条件的列表 | P1  |
| TC-LOGIN-004  | GET  | `/cms/log/login/list` | 登录日志   | 登录日志列表按时间范围无数据    | 已登录管理员 | `page=1` `size=10` `start` `end`               | 返回空列表或零条数据   | P1  |
| TC-LOGIN-005  | GET  | `/cms/log/login/list` | 登录日志   | 登录日志列表分页参数边界校验    | 已登录管理员 | `page=0` `size=0`                              | 返回参数校验失败     | P1  |
| TC-LOGIN-006  | GET  | `/cms/log/login/list` | 登录日志   | 登录日志列表页码超范围查询     | 已登录管理员 | `page=9999` `size=10`                          | 返回空列表或最后页后的空结果 | P2  |
| TC-LOGIN-007  | GET  | `/cms/log/login/list` | 登录日志   | 登录日志列表未登录访问       | 未登录    | `page=1` `size=10`                             | 返回未认证错误      | P1  |
| TC-LOGIN-008  | GET  | `/cms/log/login/list` | 登录日志   | 登录日志列表普通用户无权限访问   | 普通用户   | `page=1` `size=10`                             | 返回权限不足错误     | P1  |
| TC-LOGIN-009  | GET  | `/cms/log/login/list` | 登录日志   | 登录日志列表非法时间格式校验    | 已登录管理员 | `page=1` `size=10` `start=2026-13-40` `end=abc` | 返回参数校验失败     | P1  |
| TC-LOGIN-010  | GET  | `/cms/log/login/{id}` | 登录日志详情 | 查询单条登录日志成功        | 已登录管理员 | `id=1`                                         | 返回登录日志详情     | P1  |
| TC-LOGIN-011  | GET  | `/cms/log/login/{id}` | 登录日志详情 | 查询单条登录日志不存在失败     | 已登录管理员 | `id=9999`                                      | 返回记录不存在提示    | P1  |
| TC-LOGIN-012  | GET  | `/cms/log/login/{id}` | 登录日志详情 | 查询单条登录日志非法ID失败    | 已登录管理员 | `id=abc` / `id=0`                              | 返回参数校验失败     | P1  |
| TC-LOGIN-013  | GET  | `/cms/log/login/{id}` | 登录日志详情 | 未登录查询单条登录日志失败     | 未登录    | `id=1`                                         | 返回未认证错误      | P1  |
| TC-LOGIN-014  | GET  | `/cms/log/login/{id}` | 登录日志详情 | 无权限查询单条登录日志失败     | 普通用户   | `id=1`                                         | 返回权限不足错误     | P1  |
| TC-LOGIN-015  | DELETE | `/cms/log/login/{id}` | 删除日志   | 删除登录日志成功          | 已登录管理员 | `id=1`                                         | 删除成功         | P2  |
| TC-LOGIN-016  | DELETE | `/cms/log/login/{id}` | 删除日志   | 删除不存在的登录日志失败      | 已登录管理员 | `id=9999`                                      | 返回记录不存在提示    | P1  |
| TC-LOGIN-017  | DELETE | `/cms/log/login/{id}` | 删除日志   | 删除登录日志非法ID失败      | 已登录管理员 | `id=abc` / `id=0`                              | 返回参数校验失败     | P1  |
| TC-LOGIN-018  | DELETE | `/cms/log/login/{id}` | 删除日志   | 未登录删除登录日志失败       | 未登录    | `id=1`                                         | 返回未认证错误      | P1  |
| TC-LOGIN-019  | DELETE | `/cms/log/login/{id}` | 删除日志   | 无权限删除登录日志失败       | 普通用户   | `id=1`                                         | 返回权限不足错误     | P1  |
| TC-LOGIN-020  | DELETE | `/cms/log/login/all`  | 清空日志   | 删除所有登录日志成功        | 已登录管理员 | 无                                              | 清空成功         | P2  |
| TC-LOGIN-021  | DELETE | `/cms/log/login/all`  | 清空日志   | 未登录清空登录日志失败       | 未登录    | 无                                              | 返回未认证错误      | P1  |
| TC-LOGIN-022  | DELETE | `/cms/log/login/all`  | 清空日志   | 无权限清空登录日志失败       | 普通用户   | 无                                              | 返回权限不足错误     | P1  |


## 回归建议

- 核心查询：`TC-LOGIN-001`、`TC-LOGIN-010`
- 失败场景：`TC-LOGIN-011`、`TC-LOGIN-012`、`TC-LOGIN-013`、`TC-LOGIN-014`、`TC-LOGIN-016`、`TC-LOGIN-017`
- 清理类：`TC-LOGIN-015`、`TC-LOGIN-020`、`TC-LOGIN-021`、`TC-LOGIN-022`
