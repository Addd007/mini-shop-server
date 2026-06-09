# 订单测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：订单提交、订单列表、订单详情、支付预订单、支付回调

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| TC-ORDER-001 | POST | `/v1/order` | 提交订单 | 用户提交订单成功 | 已登录 alice | `products=[{product_id:1,count:1}]` | 提交成功，返回订单号和订单ID | P0 |
| TC-ORDER-002 | GET | `/v1/order/{id}` | 订单详情 | 查询订单详情成功 | 已登录 | `id=1` | 返回订单详情 | P0 |
| TC-ORDER-003 | GET | `/v1/order` | 订单列表 | 查询订单列表成功 | 已登录 | `page=1` `size=10` | 返回订单分页列表 | P1 |
| TC-ORDER-004 | POST | `/v1/pay/pre_order` | 预支付 | 查询预订单成功 | 已登录并有待支付订单 | 无或按接口要求传参 | 返回预支付信息 | P0 |
| TC-ORDER-005 | POST | `/v1/pay/notify` | 支付回调 | 接收微信平台支付结果 | 已有模拟回调报文 | 支付通知参数 | 回调处理成功 | P0 |
| TC-ORDER-006 | POST | `/v1/pay/re_notify` | 支付重通知 | 重试支付回调处理成功 | 已有模拟回调报文 | 支付通知参数 | 重试处理成功 | P1 |
| TC-ORDER-007 | POST | `/v1/pay/concurrency` | 并发支付 | 并发支付场景处理 | 已有待测订单 | 无或按接口要求传参 | 并发处理无异常 | P1 |
| TC-ORDER-008 | POST | `/v1/order` | 库存校验 | 库存不足时提交订单 | 已登录 alice | `products=[{product_id:3,count:1}]` | 返回库存不足或下单失败 | P0 |
| TC-ORDER-009 | GET | `/v1/order/{id}` | 边界查询 | 查询不存在的订单 | 已登录 | `id=9999` | 返回空或 404 类结果 | P2 |
| TC-ORDER-010 | GET | `/v1/order` | 分页查询 | 订单分页参数校验 | 已登录 | `page=1` `size=100` | 返回正确分页结果 | P2 |

## 回归建议

- 核心冒烟：`TC-ORDER-001`、`TC-ORDER-002`、`TC-ORDER-004`、`TC-ORDER-008`
- 支付链路：`TC-ORDER-005`、`TC-ORDER-006`、`TC-ORDER-007`
