# test_bug/1号   bug总览


| bug编号                                | bug简述名                                                                         | 严重级 | 优先级 | 状态  |
| ------------------------------------ | ------------------------------------------------------------------------------ | --- | --- | --- |
| BUG-TOKEN-VERIFY-001                 | 登录接口返回的 token 无法被 `/v1/token/verify` 正常解析                                      | 高   | P0  | 已修复 |
| BUG-AUTH-002                         | `identity.verified = 0` 的账号仍可通过登录接口获取 token                                    | 中   | P1  | 已定位 |
| BUG-AUTH-CLIENT-TYPE-001             | `POST /v1/token` 传入 `type=999` 时未返回参数校验错误，而是返回服务器端异常                           | 中   | P1  | 已修复 |
| BUG-AUTH-USERNAME-CASE-001           | `POST /v1/token` 用户名大小写不匹配时仍登录成功                                               | 中   | P2  | 已修复 |
| BUG-AUTH-USER-DELETED-001            | `POST /v1/token` 当 identity 存在但对应 user 被删除时返回服务器端异常                            | 中   | P1  | 已修复 |
| BUG-ORDER-PLACE-001                  | `POST /v1/order` 下单时访问不存在的 `main_img_url` 属性导致服务器端异常                           | 高   | P0  | 已修复 |
| BUG-PAY-STATUS-001                   | `POST /v1/pay/pre_order` 因订单状态与枚举对象直接比较，导致任意状态的订单均返回“订单已支付”                    | 高   | P0  | 已修复 |
| BUG-PAY-PREORDER-001                 | `POST /v1/pay/pre_order` 通过订单校验后进入未实现的微信预支付逻辑并返回服务器端异常                         | 高   | P0  | 已定位 |
| BUG-PAY-ORDER-NOTFOUND-001           | `POST /v1/pay/pre_order` 查询不存在订单时返回“订单类通用错误”，无法明确说明订单不存在                       | 低   | P2  | 已修复 |
| BUG-PROD-REORDER-001                 | `PUT /v1/product/{id}/reorder` 未正确校验相同顺序和超范围顺序，可能返回错误提示或错误移动图片                 | 中高  | P1  | 已定位 |
| BUG-PROD-UPDATE-001                  | `PUT /v1/product/{id}` 更新商品接口为空实现，返回成功但商品数据未变化                                 | 中高  | P1  | 已定位 |
| BUG-USER-IDENTITY-001                | `/v1/user/bind` 与 `/v1/user/unbind` 在操作站内账号身份时返回服务器端异常                         | 高   | P1  | 已修复 |
| BUG-USER-PASSWORD-MSG-001            | 密码参数校验失败时提示“包含字符、数字和 _”，与实际正则规则不一致                                             | 低   | P2  | 已修复 |
| BUG-USER-REGISTER-REUSE-001          | 账号删除后再次注册与旧账号同名时返回 1007 服务器端异常                                                 | 高   | P1  | 初修复 |
| BUG-USER-BIND-DUPLICATE-IDENTITY-001 | `PUT /v1/user/bind` 绑定已存在的邮箱/手机号/用户名时触发唯一索引异常并返回服务器端异常，同时同一用户可重复绑定多个账号导致身份关系混乱 | 中   | P1  | 已修复 |
| BUG-USER-CHANGE-PASSWORD-001         | `PUT /v1/user/password` 修改密码时可能返回成功但数据库密码未更新，或旧密码正确却返回密码错误                     | 中   | P1  | 已修复 |
| BUG-USER-DELETE-001                  | 注销当前账号接口返回 999 服务器端异常                                                          | 高   | P1  | 已修复 |
| BUG-USER-UPDATE-SAME-IDENTITY-001    | `PUT /v1/user` 更新自身资料时，用户名/手机号/邮箱与原值相同被误判为已使用，修复过程中还触发唯一索引服务器异常                | 中   | P1  | 已修复 |
| BUG-ID-VALIDATION-001                | 多个传 `id` 的接口在非法路径参数下返回 404，而不是参数格式错误                                           | 中高  | P1  | 已修复 |
| BUG-LOGIN-LOG-001                    | `GET /cms/log/login/list` 在非法时间参数下仍返回 200 和空列表                                 | 中高  | P1  | 已定位 |


14条已修复  5条已定位  1条初修复