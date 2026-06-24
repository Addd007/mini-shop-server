# 系统测试 — 恢复测试用例

> 责任人：2号  
> 测试基线：`tests/system/test_recovery.py`（4号系统测试分工）  
> 覆盖范围：服务kill后重启恢复、数据库断连自动重连、订单事务回滚验证

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 正向查询、Token验证 |
| 普通用户 | `user` | `123456` | 下单、用户信息查询 |

## 场景说明

| 场景 | 测试类型 | 说明 |
|------|---------|------|
| S-09 | 服务恢复 | Kill Flask进程 → 验证不可达 → 重启 → 验证Token有效+数据完整 |
| S-10 | 数据库恢复 | Kill MySQL连接 → 验证SQLAlchemy自动重连 |
| S-11 | 事务回滚 | 异常下单 → 验证order和order_product表无脏数据 |

---

## S-09: 服务kill后重启验证

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SYS-RECOV-001 | — | — | 服务Kill | 查找所有Flask进程并强制终止 | 服务正常运行 | 通过psutil遍历python进程，匹配`server.py`路径 | `_find_all_flask_pids()`返回非空列表，`_force_free_port()`释放端口5000 | P0 |
| TC-SYS-RECOV-002 | GET | `/v1/product/1` | 服务不可达 | Kill后服务不可达验证 | Flask进程已全部终止 | 无，直接使用requests库发起连接 | 5次尝试均返回`ConnectionError`（连接被拒绝） | P0 |
| TC-SYS-RECOV-003 | GET | `/health` | 服务重启 | 重启Flask后服务就绪 | 端口5000已释放 | 启动`python server.py run`子进程 | 30秒内`/health`返回200，`status=ok` | P0 |
| TC-SYS-RECOV-004 | GET | `/v1/product/1` | 数据完整性 | 重启后产品数据与kill前一致 | 服务已重启就绪 | 使用super token请求产品详情 | 返回200，`id`和`name`与kill前一致 | P0 |
| TC-SYS-RECOV-005 | GET | `/v1/user` | Token持久性 | 重启后kill前的Token仍然有效 | 服务已重启，持有kill前签发的token | 使用kill前获取的user token | 返回200（itsdangerous签名token不依赖服务端session） | P1 |
| TC-SYS-RECOV-006 | GET | `/v1/order` | 订单完整性 | 重启后数据库订单数据不丢失 | 服务已重启就绪 | 直连MySQL查询order表 | `SELECT COUNT(*)` 结果 > 0，订单数据完整 | P1 |

---

## S-10: 数据库断连恢复

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SYS-RECOV-007 | GET | `/v1/product/recent` | 连接池恢复 | Kill MySQL连接后SQLAlchemy自动重连 | 服务正常运行，基线请求200 | 1. `SHOW PROCESSLIST` 找到Flask→zerd的连接 2. `KILL CONNECTION <id>` 终止连接 3. 连续10次GET请求 | 前几个请求可能500（pool中无效连接），后续自动创建新连接恢复200；10次中≥5次成功 | P1 |
| TC-SYS-RECOV-008 | — | — | 手动断连 | MySQL服务完全停止再启动后恢复 | 需管理员权限（测试脚本中仅记录步骤） | `net stop MySQL80` → 请求返回500 → `net start MySQL80` → 等待30s | 数据库恢复后服务自动重连，接口恢复正常 | P2 |

---

## S-11: 订单事务回滚验证

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SYS-RECOV-009 | POST | `/v1/order` | 商品不存在 | 下单不存在的商品触发OrderException | 已登录user，记录order和order_product表基线行数 | `{"products":[{"product_id":99999,"count":1}]}` | 返回400，order和order_product表行数不变（事务回滚） | P0 |
| TC-SYS-RECOV-010 | POST | `/v1/order` | 库存不足 | 下单库存不足商品事务回滚 | 已登录user，记录基线行数，查找stock=0的商品 | `{"products":[{"product_id":<stock=0商品id>,"count":100}]}` | 返回200但`data.pass=false` `data.order_id=-1`，order和order_product表行数不变 | P0 |
| TC-SYS-RECOV-011 | POST | `/v1/order` | 缺少参数 | 下单缺少products字段参数校验 | 已登录user，记录基线行数 | `{}`（空body，缺少products字段） | 返回400，order和order_product表行数不变 | P1 |
| TC-SYS-RECOV-012 | POST | `/v1/order` | 正常下单(对照) | 正常下单order和order_product各+1 | 已登录user，用户有配送地址，记录基线行数 | `{"products":[{"product_id":1,"count":1}]}` | 返回200，order表行数+1，order_product表行数+1 | P0 |

---

## 回归建议

- 核心冒烟：`TC-SYS-RECOV-001`、`TC-SYS-RECOV-009`、`TC-SYS-RECOV-012`
- 服务恢复：`TC-SYS-RECOV-002` ~ `TC-SYS-RECOV-006`
- 数据库恢复：`TC-SYS-RECOV-007`、`TC-SYS-RECOV-008`
- 事务回滚：`TC-SYS-RECOV-010`、`TC-SYS-RECOV-011`
- 完整回归：全部 12 条
