drop database if exists zerd;

create database zerd default charset utf8mb4;

USE zerd;

SET FOREIGN_KEY_CHECKS = 0;

create table image
(
    id          int auto_increment
        primary key,
    url         varchar(255)      not null comment '图片路径',
    `from`      tinyint default 1 not null comment '1 来自本地，2 来自公网',
    create_time int               null comment '创建时间',
    update_time int               null comment '更新时间',
    delete_time int               null comment '删除时间'
)
    comment '图片总表';

create table `group`
(
    id   int auto_increment
        primary key,
    name varchar(60)  null comment '权限组名称',
    info varchar(255) null comment '权限组描述'
);

create table route
(
    id        int auto_increment comment '路由节点ID'
        primary key,
    parent_id int          not null comment '路由节点父级ID',
    title     varchar(20)  not null comment '路由节点标签',
    name      varchar(20)  null comment '路由节点名',
    icon      varchar(100) null comment '图标',
    path      varchar(100) not null comment '路由节点相对路径',
    component varchar(100) null comment '组件路径',
    hidden    tinyint(1)   not null comment '路由节点是否隐藏',
    `order`   int          null comment '路由顺序',
    constraint name
        unique (name)
);

create table user
(
    id          int auto_increment
        primary key,
    nickname    varchar(50)  null comment '昵称',
    auth        smallint     null comment '权限',
    group_id    int          null comment '用户所属的权限组id',
    avatar      varchar(255) null comment '头像URL',
    extend      varchar(255) null comment '额外备注',
    create_time int          null comment '创建时间',
    update_time int          null comment '更新时间',
    delete_time int          null comment '删除时间'
);

create index id
    on user (id);

create table banner
(
    id          int(10) auto_increment
        primary key,
    name        varchar(50)  null comment 'Banner名称，通常作为标识',
    description varchar(255) null comment 'Banner描述',
    create_time int          null,
    update_time int          null,
    delete_time int          null
)
    comment 'banner管理';

create table category
(
    id           int auto_increment
        primary key,
    name         varchar(50)  not null comment '分类名称',
    topic_img_id int          null comment '外键，关联image表',
    description  varchar(100) null comment '描述',
    create_time  int          null comment '创建时间',
    update_time  int          null comment '更新时间',
    delete_time  int          null comment '删除时间'
)
    comment '商品类目';

create table config
(
    id     int auto_increment
        primary key,
    name   varchar(64) null comment '名称',
    `key`  varchar(64) null comment '键名',
    value  varchar(64) null comment '键值',
    type   tinyint(1)  null comment '是否系统内置(True是, False否)',
    remark text        null comment '备注'
);

create table dict
(
    id         int auto_increment
        primary key,
    `order`    int         not null comment '字典排序',
    label      varchar(64) null comment '字典标签',
    value      varchar(64) null comment '字典键值',
    type       varchar(64) null comment '字典类型',
    css_class  varchar(64) null comment '样式属性（其他样式扩展）',
    list_class varchar(64) null comment '表格回显样式',
    is_default tinyint(1)  null comment '是否默认(True是, False否)',
    status     tinyint(1)  null comment '状态(True正常, False停用)',
    remark     text        null comment '备注'
);

create table dict_type
(
    id     int auto_increment
        primary key,
    name   varchar(64) null comment '字典名称',
    type   varchar(64) null comment '字典类型',
    status tinyint(1)  null comment '状态(True正常, False停用)',
    remark text        null comment '备注'
);

create table third_app
(
    id                int auto_increment
        primary key,
    app_id            varchar(64)  not null comment '应用app_id',
    app_secret        varchar(64)  not null comment '应用secret',
    app_description   varchar(100) null comment '应用程序描述',
    scope             varchar(20)  not null comment '应用权限',
    scope_description varchar(100) null comment '权限描述',
    create_time       int          null comment '创建时间',
    update_time       int          null comment '更新时间',
    delete_time       int          null comment '删除时间'
)
    comment '访问API的各应用账号密码表';

create table theme
(
    id           int auto_increment
        primary key,
    name         varchar(50)  not null comment '专题名称',
    description  varchar(255) null comment '专题描述',
    topic_img_id int          not null comment '主题图，外键',
    head_img_id  int          not null comment '专题列表页，头图',
    create_time  int          null comment '创建时间',
    update_time  int          null comment '更新时间',
    delete_time  int          null comment '删除时间'
)
    comment '主题信息表';

create table address
(
    id          int auto_increment
        primary key,
    name        varchar(30)  not null comment '收获人姓名',
    mobile      varchar(20)  not null comment '手机号',
    province    varchar(20)  null comment '省',
    city        varchar(20)  null comment '市',
    country     varchar(20)  null comment '区',
    detail      varchar(100) null comment '详细地址',
    user_id     int          not null comment '外键',
    create_time int          null comment '创建时间',
    update_time int          null comment '更新时间',
    delete_time int          null comment '删除时间',
    constraint user_id
        unique (user_id)
);

create table article
(
    id          int auto_increment
        primary key,
    author_id   int          not null comment '外键，用户id',
    type        smallint     null comment '文章类型',
    title       varchar(255) null comment '文章标题',
    summary     text         null comment '文章摘要',
    content     text         null comment '文章内容',
    theme       smallint     null comment '文章主题',
    img         varchar(255) null comment '主图路径',
    views       int          null comment '浏览量',
    create_time int          null comment '创建时间',
    update_time int          null comment '更新时间',
    delete_time int          null comment '删除时间',
    constraint article_ibfk_1
        foreign key (author_id) references user (id)
);

create index author_id
    on article (author_id);

create table auth
(
    id       int(10) auto_increment
        primary key,
    group_id int(10)     not null comment '所属权限组id',
    name     varchar(60) null comment '权限字段',
    module   varchar(50) null comment '权限的模块'
)
    comment '权限';

create table banner_item
(
    id          int auto_increment
        primary key,
    banner_id   int          null comment '外键，所属Banner组id',
    img_id      int          null comment '外键，关联image表',
    key_word    varchar(100) null comment '执行关键字，根据不同的type含义不同',
    type        smallint     null comment '跳转类型，可能导向商品，可能导向专题，可能导向其他。0，无导向；1：导向商品;2:导向专题',
    create_time int          null comment '创建时间',
    update_time int          null comment '更新时间',
    delete_time int          null comment '删除时间',
    constraint banner_item_ibfk_1
        foreign key (banner_id) references banner (id),
    constraint banner_item_ibfk_2
        foreign key (img_id) references image (id)
);

create index banner_id
    on banner_item (banner_id);

create index img_id
    on banner_item (img_id);

create table element
(
    id       int auto_increment
        primary key,
    name     varchar(50) null comment '名称',
    sign     varchar(50) null comment '元素标识',
    route_id int         not null,
    constraint element_ibfk_1
        foreign key (route_id) references route (id)
);

create index route_id
    on element (route_id);

create table file
(
    create_time int          null comment '创建时间',
    update_time int          null comment '更新时间',
    delete_time int          null comment '删除时间',
    id          int auto_increment
        primary key,
    parent_id   int          null comment '父级目录id',
    uuid_name   varchar(100) null comment '唯一名称',
    name        varchar(100) not null comment '原始名称',
    path        varchar(500) null comment '路径',
    extension   varchar(50)  null comment '后缀',
    `from`      smallint default 1 not null comment '来源: 1 本地，2 公网',
    size        int          null comment '大小',
    md5         varchar(40)  null comment '文件md5值，防止上传重复文件'
);

create table group_2_element
(
    group_id   int not null,
    element_id int not null,
    primary key (group_id, element_id),
    constraint group_2_element_ibfk_1
        foreign key (group_id) references `group` (id),
    constraint group_2_element_ibfk_2
        foreign key (element_id) references element (id)
);

create index element_id
    on group_2_element (element_id);

create table group_element
(
    group_id   int not null,
    element_id int not null,
    primary key (group_id, element_id),
    constraint group_element_ibfk_1
        foreign key (group_id) references `group` (id),
    constraint group_element_ibfk_2
        foreign key (element_id) references element (id)
);

create index element_id
    on group_element (element_id);

create table identity
(
    id          int auto_increment
        primary key,
    user_id     int          not null comment '外键，用户id',
    type        int          not null comment '登录类型',
    identifier  varchar(100) null comment '标识(手机号、邮箱、用户名或第三方应用的唯一标识)',
    credential  varchar(100) null comment '密码凭证(站内的保存密码，站外的不保存或保存token)',
    verified    smallint     null comment '是否已经验证',   
    create_time int          null comment '创建时间',
    update_time int          null comment '更新时间',
    delete_time int          null comment '删除时间',
    constraint identifier
        unique (identifier),
    constraint identity_ibfk_1
        foreign key (user_id) references user (id)
);

create index user_id
    on identity (user_id);

create table login_log
(
    id          int auto_increment
        primary key,
    user_id     int          not null comment '用户id',
    user_name   varchar(50)  null comment '用户当时的昵称',
    ip_addr     varchar(50)  null comment '登录IP地址',
    location    varchar(255) null comment '登录地点',
    browser     varchar(50)  null comment '浏览器类型',
    os          varchar(50)  null comment '操作系统',
    message     varchar(255) null comment '提示消息',
    status      tinyint(1)   null comment '登录状态(True成功, False失败)',
    create_time int          null comment '访问时间'
);

create table menu
(
    group_id int not null comment '外键 权限组ID',
    route_id int not null comment '外键 路由节点ID',
    primary key (group_id, route_id),
    constraint menu_ibfk_1
        foreign key (group_id) references `group` (id),
    constraint menu_ibfk_2
        foreign key (route_id) references route (id)
);

create index route_id
    on menu (route_id);

create table notice
(
    create_time int         null comment '创建时间',
    update_time int         null comment '更新时间',
    delete_time int         null comment '删除时间',
    id          int auto_increment
        primary key,
    type        smallint    null comment '类型(1通知, 2公告)',
    title       varchar(64) null comment '标题',
    content     text        null comment '内容',
    status      tinyint(1)  null comment '状态(0正常 1关闭)',
    remark      text        null comment '备注',
    create_by   varchar(32) null comment '创建者',
    update_by   varchar(32) null comment '更新者'
);

create table oper_log
(
    id             int auto_increment
        primary key,
    module         varchar(20)  null comment '系统模块',
    message        varchar(450) null comment '日志信息',
    user_id        int          not null comment '用户id',
    user_name      varchar(50)  null comment '用户当时的昵称',
    path           varchar(50)  null comment '请求路径',
    request_method varchar(20)  null comment '请求方法',
    request_param  json         null comment '请求参数',
    endpoint       varchar(100) null comment '端点',
    type           smallint     null comment '业务类型',
    auth           varchar(100) null comment '访问哪个权限',
    status_code    int          null comment '请求的http返回码',
    create_time    int          null comment '创建时间'
);

create table `order`
(
    id           int auto_increment
        primary key,
    order_no     varchar(20)       not null comment '订单号',
    user_id      int               not null comment '外键，用户id，注意并不是openid',
    order_status tinyint default 1 not null comment '1:未支付 2:已支付 3:已发货 4:已支付，但库存不足 ',
    snap_img     varchar(255)      null comment '订单快照·封面',
    snap_name    varchar(80)       null comment '订单快照·别名',
    snap_items   text              null comment '订单快照·详情',
    snap_address varchar(500)      null comment '订单快照·地址信息',
    total_count  int     default 0 not null comment '订单总量',
    total_price  decimal(10, 2)    not null comment '订单总价',
    prepay_id    varchar(100)      null comment '预支付ID',
    create_time  int               null comment '创建时间',
    update_time  int               null comment '更新时间',
    delete_time  int               null comment '删除时间',
    constraint order_no
        unique (order_no),
    constraint prepay_id
        unique (prepay_id)
);

create index user_id
    on `order` (user_id);

create table order_product
(
    order_id    int not null comment '联合主键，订单id',
    product_id  int not null comment '联合主键，商品id',
    count       int not null comment '商品数量',
    create_time int null comment '创建时间',
    update_time int null comment '更新时间',
    delete_time int null comment '删除时间',
    primary key (order_id, product_id)
);

create table product
(
    id           int auto_increment
        primary key,
    name         varchar(80)       not null comment '商品名称',
    price        decimal(10, 2)    not null comment '价格,单位：元',
    stock        int     default 0 not null comment '库存量',
    category_id  int               null,
    main_img_url varchar(255)      null comment '主图ID号，这是一个反范式设计，有一定的冗余',
    `from`       tinyint default 1 not null comment '图片来自 1 本地 ，2公网',
    summary      varchar(50)       null comment '摘要',
    img_id       int               null comment '图片外键',
    create_time  int               null comment '创建时间',
    update_time  int               null comment '更新时间',
    delete_time  int               null comment '删除时间'
);

create table product_image
(
    product_id  int           not null comment '商品id，外键',
    img_id      int           not null comment '外键，关联图片表',
    `order`     int default 0 not null comment '图片排序序号',
    create_time int           null comment '创建时间',
    update_time int           null comment '更新时间',
    delete_time int           null comment '删除时间',
    primary key (product_id, img_id)
);

create table product_property
(
    id          int auto_increment
        primary key,
    name        varchar(30) default '' null comment '详情属性名称',
    detail      varchar(255)           not null comment '详情属性',
    product_id  int                    not null comment '商品id，外键',
    create_time int                    null comment '创建时间',
    update_time int                    null comment '更新时间',
    delete_time int                    null comment '删除时间'
);

create table theme_product
(
    theme_id    int not null comment '主题外键',
    product_id  int not null comment '商品外键',
    create_time int null comment '创建时间',
    update_time int null comment '更新时间',
    delete_time int null comment '删除时间',
    primary key (theme_id, product_id)
)
    comment '主题所包含的商品';

SET FOREIGN_KEY_CHECKS = 1;
