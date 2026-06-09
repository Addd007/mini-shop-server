SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 基础表
-- ----------------------------

INSERT INTO `group` (id, name, info) VALUES
(1, '超级管理员', '系统最高权限组'),
(2, '普通用户组', '默认用户权限组');

INSERT INTO user (id, nickname, auth, group_id, avatar, extend, create_time, update_time, delete_time) VALUES
(1, 'admin', 1, 1, 'admin.png', '系统管理员', 1710000000, 1710000000, NULL),
(2, 'alice', 0, 2, 'alice.png', '测试用户A', 1710000100, 1710000100, NULL),
(3, 'bob', 0, 2, 'bob.png', '测试用户B', 1710000200, 1710000200, NULL);

INSERT INTO identity (id, user_id, type, identifier, credential, verified, create_time, update_time, delete_time) VALUES
(1, 1, 1, 'admin', 'admin123456', 1, 1710000000, 1710000000, NULL),
(2, 1, 2, '13800000000', 'admin123456', 1, 1710000000, 1710000000, NULL),
(3, 2, 1, 'alice', 'alice123456', 1, 1710000100, 1710000100, NULL),
(4, 2, 2, '13900000000', 'alice123456', 1, 1710000100, 1710000100, NULL),
(5, 3, 1, 'bob', 'bob123456', 1, 1710000200, 1710000200, NULL);

INSERT INTO address (id, name, mobile, province, city, country, detail, user_id, create_time, update_time, delete_time) VALUES
(1, 'Alice收', '13900000000', '广东省', '深圳市', '南山区', '科技园A座1001', 2, 1710000300, 1710000300, NULL),
(2, 'Bob收', '13700000000', '北京市', '北京市', '朝阳区', '望京SOHO T2', 3, 1710000400, 1710000400, NULL);

INSERT INTO image (id, url, `from`, create_time, update_time, delete_time) VALUES
(1, '/images/banner-1.jpg', 1, 1710000000, 1710000000, NULL),
(2, '/images/banner-2.jpg', 1, 1710000000, 1710000000, NULL),
(3, '/images/banner-3.jpg', 1, 1710000000, 1710000000, NULL),
(4, '/images/category-phone.jpg', 1, 1710000000, 1710000000, NULL),
(5, '/images/category-laptop.jpg', 1, 1710000000, 1710000000, NULL),
(6, '/images/product-1-main.jpg', 1, 1710000000, 1710000000, NULL),
(7, '/images/product-1-1.jpg', 1, 1710000000, 1710000000, NULL),
(8, '/images/product-1-2.jpg', 1, 1710000000, 1710000000, NULL),
(9, '/images/product-2-main.jpg', 1, 1710000000, 1710000000, NULL),
(10, '/images/product-2-1.jpg', 1, 1710000000, 1710000000, NULL),
(11, '/images/theme-1-topic.jpg', 1, 1710000000, 1710000000, NULL),
(12, '/images/theme-1-head.jpg', 1, 1710000000, 1710000000, NULL);

INSERT INTO banner (id, name, description, create_time, update_time, delete_time) VALUES
(1, '首页轮播', '首页 Banner 图集', 1710000000, 1710000000, NULL);

INSERT INTO banner_item (id, banner_id, img_id, key_word, type, create_time, update_time, delete_time) VALUES
(1, 1, 1, 'product-1', 1, 1710000000, 1710000000, NULL),
(2, 1, 2, 'theme-1', 2, 1710000000, 1710000000, NULL),
(3, 1, 3, 'catalog', 0, 1710000000, 1710000000, NULL);

INSERT INTO category (id, name, topic_img_id, description, create_time, update_time, delete_time) VALUES
(1, '手机', 4, '智能手机分类', 1710000000, 1710000000, NULL),
(2, '电脑', 5, '笔记本电脑分类', 1710000000, 1710000000, NULL);

INSERT INTO config (id, name, `key`, value, type, remark) VALUES
(1, '站点名称', 'site_name', 'Mini Shop', 1, '测试站点名称'),
(2, '上传目录', 'upload_dir', '/uploads', 1, '文件上传默认目录');

INSERT INTO dict_type (id, name, type, status, remark) VALUES
(1, '订单状态', 'order_status', 1, '订单状态字典'),
(2, '用户类型', 'user_type', 1, '用户类型字典');

INSERT INTO dict (id, `order`, label, value, type, css_class, list_class, is_default, status, remark) VALUES
(1, 1, '未支付', '1', 'order_status', '', 'info', 1, 1, '订单未支付'),
(2, 2, '已支付', '2', 'order_status', '', 'success', 0, 1, '订单已支付'),
(3, 3, '已发货', '3', 'order_status', '', 'warning', 0, 1, '订单已发货'),
(4, 1, '普通用户', '0', 'user_type', '', '', 1, 1, '普通用户'),
(5, 2, '管理员', '1', 'user_type', '', '', 0, 1, '管理员');

INSERT INTO third_app (id, app_id, app_secret, app_description, scope, scope_description, create_time, update_time, delete_time) VALUES
(1, 'wxapp_test_appid', 'wxapp_test_secret', '微信小程序测试应用', 'user', '基础用户权限', 1710000000, 1710000000, NULL);

INSERT INTO route (id, parent_id, title, name, icon, path, component, hidden, `order`) VALUES
(1, 0, '系统管理', 'system', 'setting', '/system', 'Layout', 0, 1),
(2, 1, '用户管理', 'user_manage', 'user', 'user', 'system/user/index', 0, 1),
(3, 1, '权限管理', 'permission_manage', 'lock', 'permission', 'system/permission/index', 0, 2),
(4, 0, '商品管理', 'product_manage', 'shop', '/product', 'Layout', 0, 2);

INSERT INTO element (id, name, sign, route_id) VALUES
(1, '新增用户', 'system.user.add', 2),
(2, '编辑用户', 'system.user.edit', 2),
(3, '删除用户', 'system.user.delete', 2),
(4, '新增权限', 'system.permission.add', 3),
(5, '删除权限', 'system.permission.delete', 3);

INSERT INTO menu (group_id, route_id) VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(2, 4);

INSERT INTO group_2_element (group_id, element_id) VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(1, 5);

INSERT INTO group_element (group_id, element_id) VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(1, 5);

INSERT INTO auth (id, group_id, name, module) VALUES
(1, 1, 'user:add', 'user'),
(2, 1, 'user:edit', 'user'),
(3, 1, 'user:delete', 'user'),
(4, 1, 'product:add', 'product'),
(5, 2, 'product:view', 'product');

-- ----------------------------
-- 商品与专题
-- ----------------------------

INSERT INTO product (id, name, price, stock, category_id, main_img_url, `from`, summary, img_id, create_time, update_time, delete_time) VALUES
(1, 'iPhone 15', 6999.00, 100, 1, '/images/product-1-main.jpg', 1, '苹果旗舰手机', 6, 1710000000, 1710000000, NULL),
(2, 'ThinkPad X1', 12999.00, 50, 2, '/images/product-2-main.jpg', 1, '轻薄商务本', 9, 1710000000, 1710000000, NULL),
(3, '小米充电宝', 199.00, 300, 1, '/images/product-3-main.jpg', 1, '便携移动电源', NULL, 1710000000, 1710000000, NULL);

INSERT INTO product_image (product_id, img_id, `order`, create_time, update_time, delete_time) VALUES
(1, 6, 0, 1710000000, 1710000000, NULL),
(1, 7, 1, 1710000000, 1710000000, NULL),
(1, 8, 2, 1710000000, 1710000000, NULL),
(2, 9, 0, 1710000000, 1710000000, NULL),
(2, 10, 1, 1710000000, 1710000000, NULL);

INSERT INTO product_property (id, name, detail, product_id, create_time, update_time, delete_time) VALUES
(1, '颜色', '黑色', 1, 1710000000, 1710000000, NULL),
(2, '存储', '256G', 1, 1710000000, 1710000000, NULL),
(3, '颜色', '深空灰', 2, 1710000000, 1710000000, NULL),
(4, '内存', '16G', 2, 1710000000, 1710000000, NULL);

INSERT INTO theme (id, name, description, topic_img_id, head_img_id, create_time, update_time, delete_time) VALUES
(1, '开学季精选', '开学季特惠活动', 11, 12, 1710000000, 1710000000, NULL),
(2, '数码好物节', '数码产品专题活动', 11, 12, 1710000000, 1710000000, NULL);

INSERT INTO theme_product (theme_id, product_id, create_time, update_time, delete_time) VALUES
(1, 1, 1710000000, 1710000000, NULL),
(1, 2, 1710000000, 1710000000, NULL),
(2, 1, 1710000000, 1710000000, NULL),
(2, 3, 1710000000, 1710000000, NULL);

INSERT INTO category (id, name, topic_img_id, description, create_time, update_time, delete_time) VALUES
(3, '配件', NULL, '手机配件分类', 1710000000, 1710000000, NULL);

-- ----------------------------
-- 文件
-- ----------------------------

INSERT INTO file (id, parent_id, uuid_name, name, path, extension, `from`, size, md5, create_time, update_time, delete_time) VALUES
(1, NULL, 'f_0001', 'banner-1.jpg', 'banner-1.jpg', 'jpg', 1, 120345, 'md5banner1', 1710000000, 1710000000, NULL),
(2, NULL, 'f_0002', 'product-1-main.jpg', 'product-1-main.jpg', 'jpg', 1, 223456, 'md5product1', 1710000000, 1710000000, NULL),
(3, NULL, 'f_0003', 'resume.pdf', 'docs/resume.pdf', 'pdf', 1, 52345, 'md5resume', 1710000000, 1710000000, NULL);

-- ----------------------------
-- 日志
-- ----------------------------

INSERT INTO login_log (id, user_id, user_name, ip_addr, location, browser, os, message, status, create_time) VALUES
(1, 1, 'admin', '127.0.0.1', '本机', 'Chrome', 'macOS', '登录成功', 1, 1710000000),
(2, 2, 'alice', '127.0.0.1', '本机', 'Chrome', 'macOS', '登录成功', 1, 1710000100),
(3, 3, 'bob', '127.0.0.1', '本机', 'Safari', 'macOS', '密码错误', 0, 1710000200);

INSERT INTO oper_log (id, module, message, user_id, user_name, path, request_method, request_param, endpoint, type, auth, status_code, create_time) VALUES
(1, 'user', '新增用户', 1, 'admin', '/api/user', 'POST', JSON_OBJECT('nickname', 'test_user'), 'user.create', 1, 'user:add', 200, 1710000000),
(2, 'product', '查看商品列表', 2, 'alice', '/api/product', 'GET', JSON_OBJECT(), 'product.list', 2, 'product:view', 200, 1710000100);

INSERT INTO notice (id, type, title, content, status, remark, create_time, update_time, delete_time, create_by, update_by) VALUES
(1, 1, '系统通知', '欢迎使用 Mini Shop 测试环境', 0, '测试通知', 1710000000, 1710000000, NULL, 'admin', 'admin'),
(2, 2, '平台公告', '平台将于今晚进行维护', 0, '维护公告', 1710000100, 1710000100, NULL, 'admin', 'admin');

INSERT INTO article (id, author_id, type, title, summary, content, theme, img, views, create_time, update_time, delete_time) VALUES
(1, 1, 1, '测试文章一', '这是第一篇测试文章摘要', '这里是测试文章正文内容', 1, '/images/article-1.jpg', 100, 1710000000, 1710000000, NULL),
(2, 2, 2, '测试文章二', '这是第二篇测试文章摘要', '这里是第二篇测试文章正文内容', 2, '/images/article-2.jpg', 50, 1710000100, 1710000100, NULL);

-- ----------------------------
-- 订单
-- ----------------------------

INSERT INTO `order` (id, order_no, user_id, order_status, snap_img, snap_name, snap_items, snap_address, total_count, total_price, prepay_id, create_time, update_time, delete_time) VALUES
(1, '202606090001', 2, 2, '/images/product-1-main.jpg', 'iPhone 15', '{"products":[{"id":1,"name":"iPhone 15","price":6999,"count":1}]}', '{"name":"Alice收","mobile":"13900000000","detail":"科技园A座1001"}', 1, 6999.00, 'wx_prepay_0001', 1710000300, 1710000400, NULL),
(2, '202606090002', 3, 1, '/images/product-2-main.jpg', 'ThinkPad X1', '{"products":[{"id":2,"name":"ThinkPad X1","price":12999,"count":1},{"id":3,"name":"小米充电宝","price":199,"count":2}]}', '{"name":"Bob收","mobile":"13700000000","detail":"望京SOHO T2"}', 3, 13397.00, 'wx_prepay_0002', 1710000500, 1710000500, NULL);

INSERT INTO order_product (order_id, product_id, count, create_time, update_time, delete_time) VALUES
(1, 1, 1, 1710000300, 1710000400, NULL),
(2, 2, 1, 1710000500, 1710000500, NULL),
(2, 3, 2, 1710000500, 1710000500, NULL);

SET FOREIGN_KEY_CHECKS = 1;