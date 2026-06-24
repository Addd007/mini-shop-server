# 系统测试 — 稳定性与兼容性测试用例

> 责任人：2号  
> 测试基线：`tests/system/test_stability.py`（4号系统测试分工）  
> 覆盖范围：持续30分钟请求稳定性监控、4种角色×11个权限边界验证

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 全权限正向测试 |
| 管理员 | `admin` | `123456` | 管理员权限边界测试 |
| 普通用户 | `user` | `123456` | 普通用户权限边界测试 |
| 未登录 | — | — | 匿名访问边界测试 |

## 场景说明

| 场景 | 测试类型 | 说明 |
|------|---------|------|
| S-14 | 持续稳定性 | 30分钟循环请求，每5分钟采样内存/CPU/延迟/错误率（支持`STABILITY_DURATION=1800`或`-m slow`控制） |
| S-15 | 多角色兼容 | 4种角色×11个端点=44个组合，验证权限边界正确 |

---

## S-14: 持续请求稳定性测试

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SYS-STAB-001 | GET | `/v1/product/1` | 持续读 | 30分钟内持续读取产品详情 | 服务正常运行，使用super token | 每0.5s循环请求（约2次/秒） | 所有请求返回200，无500错误 | P0 |
| TC-SYS-STAB-002 | POST | `/v1/token` | 持续写 | 30分钟内持续发送登录请求 | 服务正常运行，使用super token | `{"account":"super","secret":"123456","type":100}`（每0.5s循环） | 所有请求返回200，无500错误 | P0 |
| TC-SYS-STAB-003 | GET | `/cms/server` | 资源采样 | 每5分钟采样服务器内存/CPU | 服务正常运行 | 请求服务器状态端点（返回memory.percent和cpu.percent） | 内存和CPU数据可获取（非N/A），数值在合理范围 | P1 |
| TC-SYS-STAB-004 | — | — | 成功率 | 30分钟总请求成功率≥99% | 持续请求测试完成 | 统计total_req、success_req、fail_req | `success_req / total_req ≥ 0.99`，fail_req = 0 | P0 |
| TC-SYS-STAB-005 | — | — | 内存趋势 | 30分钟内内存无明显泄漏 | 采样数据≥2个 | 对比首次和末次采样的memory_percent | 内存增长 < 20个百分点（如增长过多记录警告） | P1 |
| TC-SYS-STAB-006 | — | — | 延迟稳定 | 请求延迟在可接受范围 | 持续请求测试完成 | 统计所有请求的延迟 | 平均延迟合理，P95延迟无明显波动 | P2 |

---

## S-15: 多角色访问验证

测试矩阵：4种角色 × 11个代表性端点 = 44个组合

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SYS-STAB-007 | GET | `/v1/product/1` | 公开读 | 公开商品详情-4角色均返回200 | 无 | 无 | super=200 admin=200 user=200 anon=200 | P0 |
| TC-SYS-STAB-008 | GET | `/v1/product/recent` | 公开读 | 公开最近商品-4角色均返回200 | 无 | 无 | super=200 admin=200 user=200 anon=200 | P1 |
| TC-SYS-STAB-009 | GET | `/v1/user` | 需登录 | 用户信息-未登录返回401 | 已登录（super/admin/user） | 无 | super=200 admin=200 user=200 anon=401 | P0 |
| TC-SYS-STAB-010 | GET | `/v1/order` | 需登录 | 订单列表-未登录返回401 | 已登录（super/admin/user） | 无 | super=200 admin=200 user=200 anon=401 | P0 |
| TC-SYS-STAB-011 | GET | `/cms/menu` | 公开CMS | 菜单查询-4角色均返回200 | 无 | `group_id=1` | super=200 admin=200 user=200 anon=200 | P1 |
| TC-SYS-STAB-012 | GET | `/cms/server` | 公开CMS | 服务器状态-4角色均返回200 | 无 | 无 | super=200 admin=200 user=200 anon=200 | P1 |
| TC-SYS-STAB-013 | GET | `/cms/file/types` | 公开CMS | 文件类型-4角色均返回200 | 无 | 无 | super=200 admin=200 user=200 anon=200 | P1 |
| TC-SYS-STAB-014 | GET | `/cms/admin/list` | admin_required | 管理员列表-仅super可访问 | super拥有ADMIN=2权限 | `group_id=1` | super=200 admin=401 user=401 anon=401 | P0 |
| TC-SYS-STAB-015 | GET | `/cms/group/all` | admin_required | 权限组列表-仅super可访问 | super拥有ADMIN=2权限 | 无 | super=200 admin=401 user=401 anon=401 | P0 |
| TC-SYS-STAB-016 | GET | `/cms/log/oper/list/search` | group_required | 操作日志-仅super可访问 | super属于管理员组 | 无 | super=200 admin=401 user=401 anon=401 | P1 |
| TC-SYS-STAB-017 | GET | `/health` | 无鉴权 | 健康检查-4角色均返回200 | 无 | 无 | super=200 admin=200 user=200 anon=200 | P0 |

**权限边界说明**：
- `admin_required`：检查`auth == ScopeEnum.ADMIN(2)`，admin账号auth=1(COMMON)，无法通过
- `group_required`：检查用户所在组是否有管理员权限，普通用户和admin均无法通过
- `login_required`：任何有效token均可通过
- 无装饰器：未登录也可访问

---

## 回归建议

- 核心冒烟：`TC-SYS-STAB-001`、`TC-SYS-STAB-004`、`TC-SYS-STAB-007`、`TC-SYS-STAB-014`、`TC-SYS-STAB-017`
- 稳定性：`TC-SYS-STAB-002`、`TC-SYS-STAB-003`、`TC-SYS-STAB-005`、`TC-SYS-STAB-006`
- 权限矩阵：`TC-SYS-STAB-008` ~ `TC-SYS-STAB-013`、`TC-SYS-STAB-015`、`TC-SYS-STAB-016`
- 完整回归：全部 17 条
