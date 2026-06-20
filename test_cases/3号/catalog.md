# 商品、分类、主题与轮播完整测试用例

> **测试模块：商品目录与首页运营展示模块（Category / Product / Theme / Banner）**  
> 责任人：3号  
> 测试类型：黑盒测试、接口测试、数据库一致性测试  
> 测试基线：`zerd.sql`、实际Flask路由  
> 执行日期：2026-06-19

## 1. 公共测试数据

| 数据类型 | 测试数据 |
|---|---|
| 服务地址 | `http://127.0.0.1:5000` |
| 普通账号 | `user / 123456`，登录类型`100` |
| 分类 | ID 2果味、3蔬菜、4炒货、5点心、6粗茶、7淡饭，共6条 |
| 分类2商品 | ID `2,5,8,9,10,11,12,26` |
| 主题 | ID 1专题栏位一、2专题栏位二、3专题栏位三 |
| 主题1商品 | ID `2,5,8,10,12` |
| 轮播 | Banner ID 1“首页置顶”，4个轮播项 |
| 不存在ID | `999999` |

## 2. 完整测试用例

| 用例编号 | 用例标题 | 前置条件 | 测试数据/请求 | 执行步骤 | 预期结果 | 优先级 | 实际结果 | 判定 |
|---|---|---|---|---|---|---|---|---|
| TC-M3-CATALOG-001 | 全部分类与数据库一致 | 已执行`fake.py --scope all` | `GET /v1/category/all`；分类ID=`2~7` | 查询数据库分类总数和ID；调用接口；比较数量及ID集合 | HTTP 200；`error_code=0`；返回6条；ID集合为`{2,3,4,5,6,7}` | P0 | 返回6条，数据一致 | 通过 |
| TC-M3-CATALOG-002 | 分类分页字段正确 | 分类表有6条数据 | `GET /v1/category/list?page=1&size=3` | 发送请求；检查`total/current_page/items` | HTTP 200；`total=6`；`current_page=1`；`items`长度3 | P1 | 分页字段正确 | 通过 |
| TC-M3-CATALOG-003 | 分类详情与数据库一致 | 分类2存在 | `GET /v1/category/2`；期望名称“果味” | 查询数据库ID2；请求详情；比较ID、名称、图片 | HTTP 200；ID=2；名称=果味；图片URL非空 | P0 | 与数据库一致 | 通过 |
| TC-M3-CATALOG-004 | 查询不存在分类 | ID 999999不存在 | `GET /v1/category/999999` | 请求不存在ID并记录响应 | HTTP 404；返回资源不存在错误；无分类数据 | P1 | 返回404 | 通过 |
| TC-M3-CATALOG-005 | 分类图片地址完整 | 6个分类均配置图片 | `GET /v1/category/all` | 查询全部分类；逐条检查`image` | 每个分类均包含非空图片URL，且与image表关联一致 | P1 | 6条图片均非空 | 通过 |
| TC-M3-CATALOG-006 | 分类商品关联一致 | 分类2存在8个商品 | `GET /v1/product/all/by_category?category_id=2` | 查询数据库分类2商品ID；调用接口；比较ID集合 | HTTP 200；仅返回分类2商品；不混入其他分类 | P0 | 商品集合一致 | 通过 |
| TC-M3-CATALOG-007 | 多主题集合查询 | 主题1、2存在 | `GET /v1/theme?ids=1,2` | 发送请求并提取主题ID | HTTP 200；仅返回主题1和2；图片URL非空 | P1 | 返回ID 1、2 | 通过 |
| TC-M3-CATALOG-008 | 非法主题ID集合校验 | 无 | `GET /v1/theme?ids=1,a` | 发送包含非整数ID的请求 | HTTP 400；提示IDs格式错误；无业务数据 | P1 | 返回400 | 通过 |
| TC-M3-CATALOG-009 | 主题详情商品关联一致 | 主题1关联`2,5,8,10,12` | `GET /v1/theme/1` | 查询`theme_product`；调用详情；比较商品ID和图片 | HTTP 200；主题1商品集合一致；主题图、头图非空 | P0 | 关联及图片一致 | 通过 |
| TC-M3-CATALOG-010 | 主题分页列表鉴权 | 不携带Token | `GET /v1/theme/list?page=1&size=10` | 清空鉴权信息后请求 | HTTP 401；不得返回主题分页数据 | P1 | 返回401 | 通过 |
| TC-M3-CATALOG-011 | 轮播图及轮播项完整 | Banner 1及4个item存在 | `GET /v1/banner/1`；关键字`6,25,11,10` | 请求详情；检查名称；遍历items并核对图片、type和key_word | HTTP 200；名称“首页置顶”；4个item；图片非空、type=1、关键字一致 | P0 | 4个轮播项完整 | 通过 |
| TC-M3-CATALOG-012 | 查询不存在轮播图 | Banner 999999不存在 | `GET /v1/banner/999999` | 请求不存在轮播ID | HTTP 404；返回Banner错误；无轮播数据 | P1 | 返回404 | 通过 |

## 3. 自动化对应关系

- 数据文件：`tests/cases/3号/catalog_cases.yaml`
- 自动化脚本：`tests/api/3号/test_catalog_cases.py`
- Allure结果：`reports/allure-results/member3-catalog`
- 执行结果：12通过，0失败
