# 订单测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：订单提交、订单列表、订单详情


| 用例编号         | 接口方法 | 接口路径             | 测试点  | 用例标题        | 前置条件  | 请求数据                                | 预期结果            | 优先级 |
| ------------ | ---- | ---------------- | ---- | ----------- | ----- | ----------------------------------- | --------------- | --- |
| TC-ORDER-001 | POST | `/v1/order`      | 提交订单 | 用户提交订单成功    | 已登录用户 | `products=[{product_id:1,count:1}]` | 提交成功，返回订单号和订单ID | P0  |
| TC-ORDER-002 | POST | `/v1/order`      | 提交订单 | 商品列表参数校验失败  | 已登录用户 | `products=[]`                       | 返回 400 和参数错误    | P0  |
| TC-ORDER-003 | POST | `/v1/order`      | 提交订单 | 商品数量参数非法    | 已登录用户 | `products=[{product_id:1,count:0}]` | 返回 400 和参数错误    | P0  |
| TC-ORDER-004 | POST | `/v1/order`      | 提交订单 | 未登录提交订单失败   | 未登录   | `products=[{product_id:1,count:1}]` | 返回 401          | P0  |
| TC-ORDER-005 | GET  | `/v1/order`      | 订单列表 | 查询订单列表成功    | 已登录用户 | `page=1` `size=10`                  | 返回订单分页列表        | P1  |
| TC-ORDER-006 | GET  | `/v1/order`      | 订单列表 | 订单分页参数校验失败  | 已登录用户 | `page=0` `size=100`                 | 返回 400 和参数错误    | P2  |
| TC-ORDER-007 | GET  | `/v1/order`      | 订单列表 | 未登录查询订单列表失败 | 未登录   | `page=1` `size=10`                  | 返回 401          | P1  |
| TC-ORDER-008 | GET  | `/v1/order/{id}` | 订单详情 | 查询订单详情成功    | 已登录用户 | `id=1`                              | 返回订单详情          | P0  |
| TC-ORDER-009 | GET  | `/v1/order/{id}` | 订单详情 | 查询不存在的订单    | 已登录用户 | `id=9999`                           | 返回 404          | P2  |
| TC-ORDER-010 | GET  | `/v1/order/{id}` | 订单详情 | 非法订单ID查询失败  | 已登录用户 | `id=abc`                            | 返回 400 和参数错误    | P1  |
| TC-ORDER-011 | GET  | `/v1/order/{id}` | 订单详情 | 未登录查询订单详情失败 | 未登录   | `id=1`                              | 返回 401          | P1  |


## 回归建议

- 核心冒烟：`TC-ORDER-001`、`TC-ORDER-005`、`TC-ORDER-008`
- 参数校验：`TC-ORDER-002`、`TC-ORDER-003`、`TC-ORDER-006`、`TC-ORDER-010`
- 权限校验：`TC-ORDER-004`、`TC-ORDER-007`、`TC-ORDER-011`
- 边界查询：`TC-ORDER-009`

