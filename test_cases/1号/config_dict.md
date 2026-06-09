# 配置与字典测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：参数配置、字典类型、字典数据、按 key 查询与更新

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| TC-CFG-001 | GET | `/cms/config/list` | 配置列表 | 查询参数配置列表成功 | 已登录管理员 | `page=1` `size=10` | 返回配置分页列表 | P1 |
| TC-CFG-002 | GET | `/cms/config/{id}` | 配置详情 | 查询参数配置成功 | 已登录管理员 | `id=1` | 返回配置详情 | P1 |
| TC-CFG-003 | POST | `/cms/config` | 配置新增 | 新建参数配置成功 | 已登录管理员 | `name=站点名称` `key=site_name` `value=Mini Shop` `type=true` | 创建成功 | P1 |
| TC-CFG-004 | PUT | `/cms/config/{id}` | 配置更新 | 更新参数配置成功 | 已登录管理员 | `id=1` + 更新字段 | 更新成功 | P1 |
| TC-CFG-005 | GET | `/cms/config/key/{key}` | 按 key 查询 | 基于 key 查询配置成功 | 已登录管理员 | `key=sys.user.init_password` | 返回对应配置 | P1 |
| TC-CFG-006 | PUT | `/cms/config/key/{key}` | 按 key 更新 | 更新配置 value 成功 | 已登录管理员 | `key=sys.user.init_password` `value=123456` | 更新成功 | P1 |
| TC-DICT-001 | GET | `/cms/dict/type/list` | 字典类型列表 | 查询字典类型列表成功 | 已登录管理员 | `page=1` `size=10` | 返回字典类型分页列表 | P1 |
| TC-DICT-002 | POST | `/cms/dict/type` | 字典类型新增 | 新建字典类型成功 | 已登录管理员 | `name=用户性别` `type=sys_user_sex` `status=true` | 创建成功 | P1 |
| TC-DICT-003 | GET | `/cms/dict/list` | 字典数据列表 | 查询字典数据列表成功 | 已登录管理员 | `type=sys_user_sex` `page=1` `size=10` | 返回字典数据分页列表 | P1 |
| TC-DICT-004 | GET | `/cms/dict/all` | 字典数据查询 | 查询某类字典全部数据成功 | 已登录管理员 | `type=sys_user_sex` | 返回某类型全部字典 | P1 |
| TC-DICT-005 | POST | `/cms/dict` | 字典数据新增 | 新建字典数据成功 | 已登录管理员 | `label=男` `value=0` `type=sys_user_sex` | 创建成功 | P1 |
| TC-DICT-006 | PUT | `/cms/dict/{id}` | 字典数据更新 | 更新字典数据成功 | 已登录管理员 | `id=1` + 更新字段 | 更新成功 | P1 |

## 回归建议

- 配置回归：`TC-CFG-001`、`TC-CFG-002`、`TC-CFG-005`、`TC-CFG-006`
- 字典回归：`TC-DICT-001`、`TC-DICT-003`、`TC-DICT-004`、`TC-DICT-005`、`TC-DICT-006`
