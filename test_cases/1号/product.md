# 商品与分类测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：商品列表、商品详情、分类、最近商品、商品上下游管理

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| TC-PROD-001 | GET | `/v1/product/recent` | 最近商品 | 最近商品查询成功 | 已导入测试数据 | `count=5` | 正常返回最近商品列表 | P0 |
| TC-PROD-002 | GET | `/v1/product/{id}` | 商品详情 | 商品详情查询成功 | 已导入测试数据 | `id=1` | 返回商品详情 | P0 |
| TC-PROD-003 | GET | `/v1/product/list/by_category` | 商品列表 | 按分类查询商品列表成功 | 已导入测试数据 | `category_id=1` `page=1` `size=10` | 返回分类商品分页列表 | P0 |
| TC-PROD-004 | GET | `/v1/product/all/by_category` | 商品列表 | 查询分类下所有商品成功 | 已导入测试数据 | `category_id=1` | 返回该分类下所有商品 | P1 |
| TC-PROD-005 | POST | `/v1/product` | 商品新增 | 新增商品成功 | 已登录管理员 | 商品基础信息 | 创建成功 | P0 |
| TC-PROD-006 | PUT | `/v1/product/{id}` | 商品更新 | 更新商品信息成功 | 已登录管理员 | `id=1` + 商品更新字段 | 更新成功 | P1 |
| TC-PROD-007 | DELETE | `/v1/product/{id}` | 商品删除 | 删除商品成功 | 已登录管理员 | `id=3` | 删除成功 | P1 |
| TC-PROD-008 | PUT | `/v1/product/{id}/reorder` | 图片排序 | 商品图片顺序调整成功 | 已登录管理员 | `id=1` `src_order=1` `dest_order=2` | 排序成功 | P2 |
| TC-PROD-009 | GET | `/v1/category/all` | 分类列表 | 查询所有产品分类 | 已导入测试数据 | 无 | 返回分类列表 | P0 |
| TC-PROD-010 | GET | `/v1/category/{id}` | 分类详情 | 查询分类成功 | 已导入测试数据 | `id=1` | 返回分类详情 | P1 |

## 回归建议

- 核心冒烟：`TC-PROD-001`、`TC-PROD-002`、`TC-PROD-003`、`TC-PROD-009`
- 商品管理：`TC-PROD-005`、`TC-PROD-006`、`TC-PROD-007`、`TC-PROD-008`
