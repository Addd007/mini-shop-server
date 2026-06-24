# 系统测试 — 部署测试用例

> 责任人：2号  
> 测试基线：`tests/system/test_deployment.py`（4号系统测试分工）  
> 覆盖范围：ENV_MODE环境变量切换验证、Swagger UI/API规范/Flask-Admin可用性

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 验证服务可访问 |

## 场景说明

| 场景 | 测试类型 | 说明 |
|------|---------|------|
| S-12 | 环境切换 | 验证`ENV_MODE=dev:local` / `dev` / `prod`三种模式下配置加载正确 |
| S-13 | 文档可用 | 验证Swagger UI、`apispec_1.json`、Flask-Admin均可访问 |

---

## S-12: 环境变量切换验证

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SYS-DEPLOY-001 | GET | `/health` | dev:local模式 | `ENV_MODE=dev:local`服务启动成功 | 创建`local_secure.py`（DEBUG=True）和`local_setting.py`配置文件，端口5000空闲 | 设置环境变量`ENV_MODE=dev:local`启动Flask | 30秒内`/health`返回200 | P0 |
| TC-SYS-DEPLOY-002 | GET | `/api/nonexistent_xyz_123` | dev:local DEBUG | dev:local模式下DEBUG=True返回详细错误 | 服务在dev:local模式运行 | 请求不存在的路由 | 返回404，错误信息比生产模式更详细 | P1 |
| TC-SYS-DEPLOY-003 | GET | `/health` | dev模式 | `ENV_MODE=dev`服务启动成功 | 端口5000空闲，停止上一个模式的服务 | 设置环境变量`ENV_MODE=dev`启动Flask | 30秒内`/health`返回200 | P0 |
| TC-SYS-DEPLOY-004 | GET | `/health` | prod模式 | `ENV_MODE=prod`服务启动成功 | 端口5000空闲，停止上一个模式的服务 | 设置环境变量`ENV_MODE=prod`启动Flask | 30秒内`/health`返回200 | P0 |
| TC-SYS-DEPLOY-005 | GET | `/api/nonexistent_xyz_123` | prod隐藏详情 | prod模式下不暴露错误详情 | 服务在prod模式运行 | 请求不存在的路由 | 返回404，不暴露堆栈信息 | P1 |
| TC-SYS-DEPLOY-006 | GET | `/health` | 默认模式恢复 | 测试结束后恢复默认模式 | 端口5000空闲，ENV_MODE不设置 | 启动Flask（默认模式，加载secure.py+setting.py） | 30秒内`/health`返回200，后续测试可用 | P0 |

---

## S-13: 接口文档可用性

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SYS-DEPLOY-007 | GET | `/apidocs/` | Swagger UI | Swagger UI页面可访问 | 服务正常运行 | 无 | 返回200，响应含swagger-ui或HTML页面 | P1 |
| TC-SYS-DEPLOY-008 | GET | `/apispec_1.json` | API规范JSON | API规范JSON格式正确且包含关键路径 | 服务正常运行 | 无 | 返回200，Content-Type: application/json，包含`swagger`/`info`/`paths`字段，总路径数≥10 | P0 |
| TC-SYS-DEPLOY-009 | GET | `/apispec_1.json` | 路径完整性 | 关键接口路径抽样检查 | `/apispec_1.json`可访问 | 无 | paths中包含`/v1/token`、`/v1/user`、`/v1/order`、`/v1/product/{id}`中的≥2个 | P1 |
| TC-SYS-DEPLOY-010 | GET | `/apispec_1.json` | Tags完整性 | Swagger Tags覆盖关键模块 | `/apispec_1.json`可访问 | 无 | tags中至少包含token、user、product、order、file中的3个 | P1 |
| TC-SYS-DEPLOY-011 | GET | `/admin/` | Flask-Admin | Flask-Admin管理后台可访问 | 服务正常运行 | 无，允许重定向 | 返回200或302（重定向到登录页） | P1 |

---

## 回归建议

- 核心冒烟：`TC-SYS-DEPLOY-001`、`TC-SYS-DEPLOY-006`、`TC-SYS-DEPLOY-008`
- 环境切换：`TC-SYS-DEPLOY-002` ~ `TC-SYS-DEPLOY-005`
- 文档可用：`TC-SYS-DEPLOY-007`、`TC-SYS-DEPLOY-009` ~ `TC-SYS-DEPLOY-011`
- 完整回归：全部 11 条
