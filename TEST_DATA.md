# mini-shop-server 测试数据集（重编版）

> 文档版本：v2.0  
> 编写日期：2026-06-09  
> 适用范围：mini-shop-server 接口测试、自动化测试、回归测试、环境初始化  
> 文档状态：可执行

---

## 1. 文档说明

本文档用于直接指导测试环境的数据准备与落库。它不是测试计划，也不是测试用例清单，而是一份可以用于**环境初始化、接口测试、自动化测试复用**的测试数据基线。

> 结论：如果你们项目开发已基本稳定，**可以直接使用 `zerd.sql` 作为数据库结构底稿**，再基于本文件补充一套“测试专用数据”，用于登录、权限、商品、订单、文件上传等测试。

---

## 2. 数据使用原则

1. **基础结构可直接沿用 `zerd.sql`**：表结构、基础关联关系优先复用。
2. **测试数据需独立于开发/生产**：所有账号、商品、订单仅用于测试库。
3. **关键数据固定化**：登录账号、可售商品、基础分类、文件样本等应长期保留。
4. **异常数据可重复生成**：错误密码、伪造 Token、超大文件等按需生成。
5. **自动化优先复用**：所有自动化用例尽量引用固定测试数据，不手工临时创建。

---

## 3. 推荐落库方案

### 3.1 第一阶段：导入基础库结构

先导入 `zerd.sql`，确保表结构和原始基础数据齐全：

```sql
create database zerd_test default charset utf8mb4;
use zerd_test;
source /path/to/zerd.sql;
```

### 3.2 第二阶段：补充测试专用数据

在基础库之上补充本文件定义的测试数据，保证测试用例可直接执行。

### 3.3 第三阶段：固化自动化数据

将固定账号、商品、文件、订单样例同步到自动化测试的数据文件中，避免每次手工准备。

---

## 4. 测试数据总表

| 数据编号 | 数据类型 | 数据名称 | 建议值/内容 | 用途 | 关联用例 | 是否固定 | 是否需落库 | 备注 |
|---|---|---|---|---|---|---|---|---|
| TD-AUTH-001 | 账号 | 管理员账号 | username=admin, password=123456 | 登录、后台管理、权限测试 | TC-AUTH-001、TC-RBAC-001、TC-CFG-001 | 是 | 是 | 核心账号 |
| TD-AUTH-002 | 账号 | 普通用户账号 | username=normal_user, password=123456 | 普通用户登录、越权测试 | TC-AUTH-004、TC-USER-002、TC-RBAC-005 | 是 | 是 | 普通权限 |
| TD-AUTH-003 | 账号 | 停用账号 | username=disabled_user, password=123456 | 停用账号登录失败测试 | TC-USER-003 | 是 | 是 | 状态异常 |
| TD-AUTH-004 | 账号 | 新增测试用户 | username=test_user, password=123456 | 回归/自动化专用 | TC-AUTH-001、TC-USER-001 | 是 | 是 | 建议长期保留 |
| TD-TOKEN-001 | 鉴权 | 有效 Token | 登录成功后动态获取 | 鉴权接口测试 | TC-AUTH-004、TC-USER-001 | 否 | 否 | 运行时生成 |
| TD-TOKEN-002 | 鉴权 | 伪造 Token | fake-token-123456 | 鉴权失败测试 | TC-AUTH-005 | 否 | 否 | 安全测试 |
| TD-TOKEN-003 | 鉴权 | 过期 Token | 手工构造过期 token | 过期校验测试 | TC-AUTH-006 | 否 | 否 | 如系统支持 |
| TD-PROD-001 | 商品 | 可售商品A | 商品ID=1001, 库存=100, 状态=上架 | 商品查询、下单测试 | TC-CATALOG-001、TC-ORDER-001 | 是 | 是 | 核心交易商品 |
| TD-PROD-002 | 商品 | 可售商品B | 商品ID=1002, 库存=50, 状态=上架 | 分页、列表、下单测试 | TC-CATALOG-005、TC-CATALOG-006 | 是 | 是 | 辅助商品 |
| TD-PROD-003 | 商品 | 库存不足商品 | 商品ID=1003, 库存=0, 状态=上架 | 库存不足下单测试 | TC-ORDER-002 | 是 | 是 | 异常交易商品 |
| TD-PROD-004 | 商品 | 下架商品 | 商品ID=1004, 状态=下架 | 状态/不可见测试 | TC-CATALOG-001、TC-CATALOG-005 | 是 | 是 | 边界数据 |
| TD-CATE-001 | 分类 | 一级分类 | 类别ID=2001, 名称=测试分类A | 分类树测试 | TC-CATALOG-002 | 是 | 是 | 基础分类 |
| TD-CATE-002 | 分类 | 二级分类 | 父ID=2001, 名称=测试分类A-1 | 分类树测试 | TC-CATALOG-002 | 是 | 是 | 层级数据 |
| TD-CATE-003 | 分类 | 三级分类 | 父ID=2002, 名称=测试分类A-1-1 | 分类树测试 | TC-CATALOG-002 | 是 | 是 | 深层级数据 |
| TD-BANNER-001 | 轮播 | 轮播图A | 启用、排序=1、图片URL有效 | 轮播查询测试 | TC-CATALOG-003 | 是 | 是 | 前台展示 |
| TD-BANNER-002 | 轮播 | 轮播图B | 启用、排序=2、图片URL有效 | 轮播查询测试 | TC-CATALOG-003 | 是 | 是 | 前台展示 |
| TD-THEME-001 | 主题 | 主题详情A | 主题信息完整、状态正常 | 主题查询测试 | TC-CATALOG-004 | 是 | 是 | 如接口已实现 |
| TD-DICT-001 | 字典 | 性别字典 | 男/女/未知 | 字典查询测试 | TC-CFG-001 | 是 | 是 | 基础字典 |
| TD-DICT-002 | 字典 | 状态字典 | 启用/停用 | 状态、参数测试 | TC-CFG-001、TC-CFG-005 | 是 | 是 | 常用字典 |
| TD-PARAM-001 | 参数 | 分页大小 | page_size=10 | 参数管理测试 | TC-CFG-003 | 是 | 是 | 常用参数 |
| TD-PARAM-002 | 参数 | 默认主题色 | primary_color=#1677ff | 参数管理测试 | TC-CFG-003 | 是 | 是 | UI 配置参数 |
| TD-NOTICE-001 | 通知 | 发布通知A | 标题=系统通知A，状态=已发布 | 通知发布测试 | TC-CFG-004、TC-CFG-005 | 是 | 是 | 运营通知 |
| TD-NOTICE-002 | 通知 | 草稿通知B | 标题=草稿通知B，状态=草稿 | 状态流转测试 | TC-CFG-005 | 是 | 是 | 状态样例 |
| TD-ADDR-001 | 地址 | 默认收货地址 | 姓名=测试收件人, 手机号=13800000000, 地址=测试省测试市测试区测试路1号 | 下单测试 | TC-ORDER-001 | 是 | 是 | 核心下单依赖 |
| TD-ADDR-002 | 地址 | 备用收货地址 | 姓名=备用收件人, 手机号=13900000000, 地址=备用地址2号 | 下单测试 | TC-ORDER-001 | 是 | 是 | 备用场景 |
| TD-ORDER-001 | 订单 | 待支付订单 | 订单号=O202606090001, 状态=待支付, 金额=99.00 | 支付回调、幂等测试 | TC-ORDER-006、TC-ORDER-007、TC-ORDER-008 | 是 | 是 | 支付样例 |
| TD-ORDER-002 | 订单 | 已支付订单 | 订单号=O202606090002, 状态=已支付, 金额=99.00 | 状态流转测试 | TC-ORDER-005 | 是 | 是 | 对照样例 |
| TD-ORDER-003 | 订单 | 超时订单 | 订单号=O202606090003, 状态=超时未支付, 金额=99.00 | 超时关闭测试 | TC-ORDER-010 | 是 | 是 | 如系统支持定时任务 |
| TD-ORDER-004 | 订单 | 重复提交样例 | 同一用户同一商品同一地址 | 幂等性测试 | TC-ORDER-003 | 否 | 是 | 运行时生成 |
| TD-FILE-001 | 文件 | 正常图片 | upload_test.png | 文件上传测试 | TC-FILE-001 | 是 | 否 | 放在 `tests/data/` |
| TD-FILE-002 | 文件 | 正常文档 | test_doc.txt / test_doc.pdf | 文件上传测试 | TC-FILE-001、TC-FILE-005 | 是 | 否 | 放在 `tests/data/` |
| TD-FILE-003 | 文件 | 非法格式文件 | test_script.exe | 非法格式拦截测试 | TC-FILE-002 | 是 | 否 | 放在 `tests/data/` |
| TD-FILE-004 | 文件 | 超大文件 | large_file.bin | 大小限制测试 | TC-FILE-003 | 是 | 否 | 放在 `tests/data/` |
| TD-FILE-005 | 文件 | 空文件 | empty.txt | 空文件拦截测试 | TC-FILE-007 | 是 | 否 | 放在 `tests/data/` |
| TD-FILE-006 | 文件 | 中文/特殊字符文件名 | 测试图片-01.png | 文件名兼容性测试 | TC-FILE-006 | 是 | 否 | 放在 `tests/data/` |
| TD-ERR-001 | 异常 | 错误密码 | admin + wrong-password | 登录失败测试 | TC-AUTH-002 | 否 | 否 | 运行时构造 |
| TD-ERR-002 | 异常 | 空参数 | username/password 为空 | 参数校验测试 | TC-AUTH-003 | 否 | 否 | 运行时构造 |
| TD-ERR-003 | 异常 | 错误金额报文 | amount 与订单金额不一致 | 支付金额校验测试 | TC-ORDER-008 | 否 | 否 | 运行时构造 |
| TD-ERR-004 | 异常 | 超长字段 | 超长用户名/超长通知标题 | 边界测试 | TC-USER-005、TC-CFG-006 | 否 | 否 | 运行时构造 |

---

## 5. 建议数据库表与数据内容

下面是建议重点准备数据的表及用途说明。字段名请以项目实际表结构为准。

| 表名/模块 | 建议准备的数据 | 用途 | 说明 |
|---|---|---|---|
| user | admin、normal_user、disabled_user、test_user | 登录、权限、用户信息测试 | 核心账号表 |
| role | admin_role、user_role、readonly_role | RBAC 测试 | 角色权限矩阵 |
| permission / menu | 菜单树、按钮权限 | 权限控制与菜单测试 | 前后端联动 |
| product | 可售商品、库存不足商品、下架商品 | 商品查询、下单测试 | 核心业务表 |
| category | 多级分类 | 分类树测试 | 支持层级查询 |
| banner | 启用轮播、停用轮播 | 前台展示测试 | 排序与状态 |
| theme | 主题数据 | 主题查询测试 | 如接口已实现 |
| dict | 性别、状态、类型字典 | 基础配置测试 | 常用配置项 |
| param / setting | 分页大小、主题色等参数 | 参数管理测试 | 配置生效验证 |
| notice | 已发布/草稿通知 | 通知管理测试 | 状态流转 |
| address | 默认地址、备用地址 | 订单测试 | 下单前置数据 |
| order | 待支付、已支付、超时订单 | 订单/支付测试 | 幂等与状态流转 |
| log | 登录日志、操作日志 | 审计验证 | 通常由接口执行生成 |

---

## 6. 文件数据准备建议

建议在 `tests/data/` 下准备以下文件：

```text
tests/data/
├── upload_test.png
├── test_doc.txt
├── test_doc.pdf
├── test_script.exe
├── large_file.bin
├── empty.txt
└── 测试图片-01.png
```

### 6.1 文件用途

| 文件名 | 类型 | 用途 |
|---|---|---|
| upload_test.png | 图片 | 合法上传测试 |
| test_doc.txt | 文本 | 文档上传测试 |
| test_doc.pdf | PDF | 文档上传测试 |
| test_script.exe | 可执行文件 | 非法格式拦截测试 |
| large_file.bin | 大文件 | 大小限制测试 |
| empty.txt | 空文件 | 空文件拦截测试 |
| 测试图片-01.png | 特殊文件名 | 文件名兼容性测试 |

---

## 7. 自动化测试推荐数据文件

如果你们要做 YAML 驱动自动化，建议同步生成以下数据文件：

```text
tests/data/
├── accounts.yaml
├── products.yaml
├── categories.yaml
├── orders.yaml
├── files.yaml
├── dicts.yaml
├── params.yaml
├── notices.yaml
└── invalid_cases.yaml
```

---

## 8. YAML 数据样例

### 8.1 `accounts.yaml`

```yaml
admin:
  username: admin
  password: "123456"
  role: admin

normal_user:
  username: normal_user
  password: "123456"
  role: user

disabled_user:
  username: disabled_user
  password: "123456"
  role: disabled

test_user:
  username: test_user
  password: "123456"
  role: user
```

### 8.2 `products.yaml`

```yaml
available_product_a:
  id: 1001
  title: 可售商品A
  stock: 100
  status: on

available_product_b:
  id: 1002
  title: 可售商品B
  stock: 50
  status: on

out_of_stock_product:
  id: 1003
  title: 库存不足商品B
  stock: 0
  status: on

off_shelf_product:
  id: 1004
  title: 下架商品
  stock: 20
  status: off
```

### 8.3 `categories.yaml`

```yaml
category_lv1:
  id: 2001
  name: 测试分类A
  parent_id: 0

category_lv2:
  id: 2002
  name: 测试分类A-1
  parent_id: 2001

category_lv3:
  id: 2003
  name: 测试分类A-1-1
  parent_id: 2002
```

### 8.4 `orders.yaml`

```yaml
pending_order:
  order_no: O202606090001
  status: pending
  amount: 99.00

paid_order:
  order_no: O202606090002
  status: paid
  amount: 99.00

timeout_order:
  order_no: O202606090003
  status: timeout
  amount: 99.00
```

### 8.5 `files.yaml`

```yaml
image_file: tests/data/upload_test.png
doc_file: tests/data/test_doc.txt
pdf_file: tests/data/test_doc.pdf
invalid_file: tests/data/test_script.exe
large_file: tests/data/large_file.bin
empty_file: tests/data/empty.txt
special_name_file: tests/data/测试图片-01.png
```

### 8.6 `invalid_cases.yaml`

```yaml
wrong_password:
  username: admin
  password: wrong-password

empty_login:
  username: ""
  password: ""

fake_token:
  token: fake-token-123456

wrong_amount:
  amount: 199.00
  order_amount: 99.00
```

---

## 9. 数据清理原则

1. 测试生成的临时订单、日志、上传文件应定期清理。
2. 固定账号、商品、分类、字典等基础数据尽量保留。
3. 如果数据被污染，优先通过重导 `zerd.sql` + 补充测试数据恢复。
4. 自动化测试应尽量避免依赖一次性手工创建的数据。

---

## 10. 最终建议

- **数据库结构**：优先直接使用 `zerd.sql`
- **测试基础数据**：按本文件补一套测试专用数据
- **自动化执行数据**：同步到 `tests/data/*.yaml`
- **临时运行数据**：Token、日志、回调、异常报文等在执行时动态生成

> 这样做的好处是：你们测试环境稳定、自动化可复用、回归成本低。
