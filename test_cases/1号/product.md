# 商品测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：商品列表、商品详情、最近商品、商品上下游管理


| 用例编号        | 接口方法   | 接口路径                           | 测试点    | 用例标题             | 前置条件    | 请求数据                                | 预期结果         | 优先级 |
| ----------- | ------ | ------------------------------ | ------ | ---------------- | ------- | ----------------------------------- | ------------ | --- |
| TC-PROD-001 | GET    | `/v1/product/recent`           | 最近商品   | 最近商品查询成功        | 已导入测试数据 | `count=5`                           | 正常返回最近商品列表    | P0  |
| TC-PROD-002 | GET    | `/v1/product/recent`           | 最近商品   | 最近商品数量参数校验失败    | 已导入测试数据 | `count=0`                           | 返回 400 和参数错误  | P1  |
| TC-PROD-003 | GET    | `/v1/product/{id}`             | 商品详情   | 商品详情查询成功         | 已导入测试数据 | `id=1`                              | 返回商品详情       | P0  |
| TC-PROD-004 | GET    | `/v1/product/{id}`             | 商品详情   | 非法商品ID返回格式错误     | 已导入测试数据 | `id=abc`                            | 返回 400 和参数错误  | P1  |
| TC-PROD-005 | GET    | `/v1/product/{id}`             | 商品详情   | 商品ID不存在返回404     | 已导入测试数据 | `id=9999`                           | 返回商品不存在      | P1  |
| TC-PROD-006 | GET    | `/v1/product/list/by_category` | 商品列表   | 按分类查询商品列表成功      | 已导入测试数据 | `category_id=1` `page=1` `size=10`  | 返回分类商品分页列表    | P0  |
| TC-PROD-007 | GET    | `/v1/product/list/by_category` | 商品列表   | 分类商品列表参数校验失败     | 已导入测试数据 | `category_id=abc` `page=1` `size=10` | 返回 400 和参数错误  | P1  |
| TC-PROD-008 | GET    | `/v1/product/list/by_category` | 商品列表   | 分类商品列表未登录访问失败    | 未登录      | `category_id=1` `page=1` `size=10`   | 返回 401        | P1  |
| TC-PROD-009 | GET    | `/v1/product/list/by_category` | 商品列表   | 分类商品列表页码边界校验失败   | 已登录管理员  | `category_id=1` `page=0` `size=10`   | 返回 400 和参数错误  | P1  |
| TC-PROD-010 | GET    | `/v1/product/list/by_category` | 商品列表   | 分类商品列表页大小边界校验失败  | 已登录管理员  | `category_id=1` `page=1` `size=0`    | 返回 400 和参数错误  | P1  |
| TC-PROD-011 | GET    | `/v1/product/all/by_category`  | 商品列表   | 查询分类下所有商品成功      | 已导入测试数据 | `category_id=1`                     | 返回该分类下所有商品    | P1  |
| TC-PROD-012 | POST   | `/v1/product`                  | 商品新增   | 新增商品成功           | 已登录管理员  | 商品基础信息                              | 创建成功         | P0  |
| TC-PROD-013 | PUT    | `/v1/product/{id}`             | 商品更新   | 更新商品信息成功        | 已登录管理员  | `id=1` + 商品更新字段                     | 更新成功         | P1  |
| TC-PROD-014 | PUT    | `/v1/product/{id}`             | 商品更新   | 非法商品ID更新失败      | 已登录管理员  | `id=0` + 商品更新字段                     | 返回 400 和参数错误  | P1  |
| TC-PROD-015 | DELETE | `/v1/product/{id}`             | 商品删除   | 删除商品成功           | 已登录管理员  | `id=3`                              | 删除成功         | P1  |
| TC-PROD-016 | DELETE | `/v1/product/{id}`             | 商品删除   | 非法商品ID删除失败      | 已登录管理员  | `id=-1`                             | 返回 400 和参数错误  | P1  |
| TC-PROD-017 | DELETE | `/v1/product/{id}`             | 商品删除   | 商品删除未登录访问失败     | 未登录      | `id=3`                              | 返回 401        | P1  |
| TC-PROD-018 | PUT    | `/v1/product/{id}/reorder`     | 图片排序   | 商品图片顺序调整成功      | 已登录管理员  | `id=1` `src_order=1` `dest_order=2` | 排序成功         | P2  |
| TC-PROD-019 | PUT    | `/v1/product/{id}/reorder`     | 图片排序   | 非法商品ID排序失败      | 已登录管理员  | `id=abc` `src_order=1` `dest_order=2` | 返回 400 和参数错误  | P1  |
| TC-PROD-020 | PUT    | `/v1/product/{id}/reorder`     | 图片排序   | 图片顺序参数非法失败      | 已登录管理员  | `id=1` `src_order=abc` `dest_order=2` | 返回 400 和参数错误  | P1  |
| TC-PROD-021 | PUT    | `/v1/product/{id}/reorder`     | 图片排序   | 图片顺序参数为空失败      | 已登录管理员  | `id=1` `src_order=1` `dest_order=`    | 返回 400 和参数错误  | P1  |


## 回归建议

- 核心冒烟：`TC-PROD-001`、`TC-PROD-002`、`TC-PROD-003`
- 商品详情：`TC-PROD-004`、`TC-PROD-005`
- 分类查询：`TC-PROD-006`、`TC-PROD-007`、`TC-PROD-008`、`TC-PROD-009`、`TC-PROD-010`、`TC-PROD-011`
- 商品新增：`TC-PROD-012`
- 商品更新：`TC-PROD-013`、`TC-PROD-014`
- 商品删除：`TC-PROD-017`、`TC-PROD-018`、`TC-PROD-019`
- 图片排序：`TC-PROD-020`、`TC-PROD-021`、`TC-PROD-022`、`TC-PROD-023`
