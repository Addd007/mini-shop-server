# _*_ coding: utf-8 _*_
"""
  Created by Allen7D on 2018/5/12.
"""
from __future__ import annotations

import argparse
from typing import Iterable

from sqlalchemy import text

from app import create_app
from app.core.db import db
from app.libs.enums import ScopeEnum
from app.models.category import Category
from app.models.identity import Identity
from app.models.image import Image
from app.models.m2m import Product2Image
from app.models.product import Product
from app.models.product_property import Product2Property
from app.models.user import User

__author__ = 'Allen7D'


PASSWORD_HASH = "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"

USER_SEEDS = [
    {"id": 1, "nickname": "超级管理员", "auth": ScopeEnum.ADMIN.value, "group_id": 1, "avatar": "http://abc/xzy.jpg", "create_time": 1588138125, "update_time": 1592674088, "delete_time": None},
    {"id": 2, "nickname": "小叶", "auth": ScopeEnum.COMMON.value, "group_id": 1, "avatar": None, "create_time": None, "update_time": 1592674088, "delete_time": None},
    {"id": 3, "nickname": "小董", "auth": ScopeEnum.COMMON.value, "group_id": 1, "avatar": None, "create_time": 1587102577, "update_time": 1592674088, "delete_time": None},
    {"id": 4, "nickname": "Allen7D", "auth": ScopeEnum.COMMON.value, "group_id": 1, "avatar": None, "create_time": None, "update_time": 1592879250, "delete_time": None},
    {"id": 24, "nickname": "Allen9D", "auth": ScopeEnum.COMMON.value, "group_id": 2, "avatar": None, "create_time": None, "update_time": None, "delete_time": None},
    {"id": 25, "nickname": "Allen8D", "auth": ScopeEnum.COMMON.value, "group_id": 2, "avatar": None, "create_time": None, "update_time": None, "delete_time": None},
    {"id": 27, "nickname": "笑呵呵", "auth": ScopeEnum.COMMON.value, "group_id": 3, "avatar": None, "create_time": 1587024920, "update_time": 1587029097, "delete_time": None},
    {"id": 30, "nickname": "宋仁投", "auth": ScopeEnum.COMMON.value, "group_id": 6, "avatar": None, "create_time": 1587043791, "update_time": 1588686249, "delete_time": None},
    {"id": 31, "nickname": "普通用户", "auth": ScopeEnum.COMMON.value, "group_id": 6, "avatar": None, "create_time": 1588134674, "update_time": 1588686249, "delete_time": None},
]

IDENTITY_SEEDS = [
    {"id": 1, "user_id": 3, "type": 101, "identifier": "666@qq.com", "credential": PASSWORD_HASH, "verified": 1, "create_time": 1586767003, "update_time": 1587019825, "delete_time": None},
    {"id": 2, "user_id": 3, "type": 200, "identifier": "oYf_s0OnCim9Cx7tCV-AHs_rDWXs", "credential": None, "verified": 1, "create_time": 1586767003, "update_time": None, "delete_time": None},
    {"id": 3, "user_id": 1, "type": 101, "identifier": "999@qq.com", "credential": PASSWORD_HASH, "verified": 1, "create_time": 1586767003, "update_time": 1592288770, "delete_time": None},
    {"id": 4, "user_id": 3, "type": 100, "identifier": "Allen7D", "credential": PASSWORD_HASH, "verified": 1, "create_time": 1586767003, "update_time": 1587019825, "delete_time": None},
    {"id": 5, "user_id": 3, "type": 102, "identifier": "13758787058", "credential": PASSWORD_HASH, "verified": 1, "create_time": 1586767003, "update_time": 1587102577, "delete_time": None},
    {"id": 7, "user_id": 2, "type": 101, "identifier": "777@qq.com", "credential": PASSWORD_HASH, "verified": 1, "create_time": 1586767003, "update_time": None, "delete_time": None},
    {"id": 8, "user_id": 27, "type": 100, "identifier": "Allen2D", "credential": PASSWORD_HASH, "verified": 0, "create_time": 1587024948, "update_time": None, "delete_time": None},
    {"id": 9, "user_id": 27, "type": 102, "identifier": "13755555555", "credential": PASSWORD_HASH, "verified": 0, "create_time": 1587024948, "update_time": 1587029097, "delete_time": None},
    {"id": 10, "user_id": 27, "type": 101, "identifier": "555@qq.com", "credential": PASSWORD_HASH, "verified": 0, "create_time": 1587024956, "update_time": None, "delete_time": None},
    {"id": 14, "user_id": 30, "type": 100, "identifier": "Allen3D", "credential": PASSWORD_HASH, "verified": 1, "create_time": 1587043791, "update_time": 1587043791, "delete_time": 1587043791},
    {"id": 15, "user_id": 30, "type": 102, "identifier": "13758787053", "credential": PASSWORD_HASH, "verified": 0, "create_time": 1587043792, "update_time": None, "delete_time": None},
    {"id": 18, "user_id": 1, "type": 102, "identifier": "19900000001", "credential": PASSWORD_HASH, "verified": 0, "create_time": 1588134197, "update_time": 1592288770, "delete_time": None},
    {"id": 19, "user_id": 31, "type": 100, "identifier": "user", "credential": PASSWORD_HASH, "verified": 1, "create_time": 1588134674, "update_time": None, "delete_time": None},
    {"id": 20, "user_id": 31, "type": 102, "identifier": "19900000003", "credential": PASSWORD_HASH, "verified": 0, "create_time": 1588134675, "update_time": None, "delete_time": None},
    {"id": 21, "user_id": 31, "type": 101, "identifier": "111@qq.com", "credential": PASSWORD_HASH, "verified": 0, "create_time": 1588134675, "update_time": None, "delete_time": None},
    {"id": 24, "user_id": 1, "type": 100, "identifier": "super", "credential": PASSWORD_HASH, "verified": 0, "create_time": 1588140875, "update_time": 1592288770, "delete_time": None},
]

PRODUCT_SEEDS = [
    {"id": 1, "name": "芹菜 半斤", "price": 0.01, "stock": 998, "category_id": 3, "main_img_url": "/product-vg@1.png", "img_id": 13},
    {"id": 2, "name": "梨花带雨 3个", "price": 0.01, "stock": 984, "category_id": 2, "main_img_url": "/product-dryfruit@1.png", "img_id": 10},
    {"id": 3, "name": "素米 327克", "price": 0.01, "stock": 996, "category_id": 7, "main_img_url": "/product-rice@1.png", "img_id": 31},
    {"id": 4, "name": "红袖枸杞 6克*3袋", "price": 0.01, "stock": 998, "category_id": 6, "main_img_url": "/product-tea@1.png", "img_id": 32},
    {"id": 5, "name": "春生龙眼 500克", "price": 0.01, "stock": 995, "category_id": 2, "main_img_url": "/product-dryfruit@2.png", "img_id": 33},
    {"id": 6, "name": "小红的猪耳朵 120克", "price": 0.01, "stock": 997, "category_id": 5, "main_img_url": "/product-cake@2.png", "img_id": 53},
    {"id": 7, "name": "泥蒿 半斤", "price": 0.01, "stock": 998, "category_id": 3, "main_img_url": "/product-vg@2.png", "img_id": 68},
    {"id": 8, "name": "夏日芒果 3个", "price": 0.01, "stock": 995, "category_id": 2, "main_img_url": "/product-dryfruit@3.png", "img_id": 36},
    {"id": 9, "name": "冬木红枣 500克", "price": 0.01, "stock": 996, "category_id": 2, "main_img_url": "/product-dryfruit@4.png", "img_id": 37},
    {"id": 10, "name": "万紫千凤梨 300克", "price": 0.01, "stock": 996, "category_id": 2, "main_img_url": "/product-dryfruit@5.png", "img_id": 38},
    {"id": 11, "name": "贵妃笑 100克", "price": 0.01, "stock": 994, "category_id": 2, "main_img_url": "/product-dryfruit-a@6.png", "img_id": 39},
    {"id": 12, "name": "珍奇异果 3个", "price": 0.01, "stock": 999, "category_id": 2, "main_img_url": "/product-dryfruit@7.png", "img_id": 40},
    {"id": 13, "name": "绿豆 125克", "price": 0.01, "stock": 999, "category_id": 7, "main_img_url": "/product-rice@2.png", "img_id": 41},
    {"id": 14, "name": "芝麻 50克", "price": 0.01, "stock": 999, "category_id": 7, "main_img_url": "/product-rice@3.png", "img_id": 42},
    {"id": 15, "name": "猴头菇 370克", "price": 0.01, "stock": 999, "category_id": 7, "main_img_url": "/product-rice@4.png", "img_id": 43},
    {"id": 16, "name": "西红柿 1斤", "price": 0.01, "stock": 999, "category_id": 3, "main_img_url": "/product-vg@3.png", "img_id": 69},
    {"id": 17, "name": "油炸花生 300克", "price": 0.01, "stock": 999, "category_id": 4, "main_img_url": "/product-fry@1.png", "img_id": 44},
    {"id": 18, "name": "春泥西瓜子 128克", "price": 0.01, "stock": 997, "category_id": 4, "main_img_url": "/product-fry@2.png", "img_id": 45},
    {"id": 19, "name": "碧水葵花籽 128克", "price": 0.01, "stock": 999, "category_id": 4, "main_img_url": "/product-fry@3.png", "img_id": 46},
    {"id": 20, "name": "碧螺春 12克*3袋", "price": 0.01, "stock": 999, "category_id": 6, "main_img_url": "/product-tea@2.png", "img_id": 47},
    {"id": 21, "name": "西湖龙井 8克*3袋", "price": 0.01, "stock": 998, "category_id": 6, "main_img_url": "/product-tea@3.png", "img_id": 48},
    {"id": 22, "name": "梅兰清花糕 1个", "price": 0.01, "stock": 997, "category_id": 5, "main_img_url": "/product-cake-a@3.png", "img_id": 54},
    {"id": 23, "name": "清凉薄荷糕 1个", "price": 0.01, "stock": 998, "category_id": 5, "main_img_url": "/product-cake-a@4.png", "img_id": 55},
    {"id": 25, "name": "小明的妙脆角 120克", "price": 0.01, "stock": 999, "category_id": 5, "main_img_url": "/product-cake@1.png", "img_id": 52},
    {"id": 26, "name": "红衣青瓜 混搭160克", "price": 0.01, "stock": 999, "category_id": 2, "main_img_url": "/product-dryfruit@8.png", "img_id": 56},
    {"id": 27, "name": "锈色瓜子 100克", "price": 0.01, "stock": 998, "category_id": 4, "main_img_url": "/product-fry@4.png", "img_id": 57},
    {"id": 28, "name": "春泥花生 200克", "price": 0.01, "stock": 999, "category_id": 4, "main_img_url": "/product-fry@5.png", "img_id": 58},
    {"id": 29, "name": "冰心鸡蛋 2个", "price": 0.01, "stock": 999, "category_id": 7, "main_img_url": "/product-rice@5.png", "img_id": 59},
    {"id": 30, "name": "八宝莲子 200克", "price": 0.01, "stock": 999, "category_id": 7, "main_img_url": "/product-rice@6.png", "img_id": 14},
    {"id": 31, "name": "深涧木耳 78克", "price": 0.01, "stock": 999, "category_id": 7, "main_img_url": "/product-rice@7.png", "img_id": 60},
    {"id": 32, "name": "土豆 半斤", "price": 0.01, "stock": 999, "category_id": 3, "main_img_url": "/product-vg@4.png", "img_id": 66},
    {"id": 33, "name": "青椒 半斤", "price": 0.01, "stock": 999, "category_id": 3, "main_img_url": "/product-vg@5.png", "img_id": 67},
]

CATEGORY_SEEDS = [
    {"id": 2, "name": "果味", "topic_img_id": 6, "description": None},
    {"id": 3, "name": "蔬菜", "topic_img_id": 5, "description": None},
    {"id": 4, "name": "炒货", "topic_img_id": 7, "description": None},
    {"id": 5, "name": "点心", "topic_img_id": 4, "description": None},
    {"id": 6, "name": "粗茶", "topic_img_id": 8, "description": None},
    {"id": 7, "name": "淡饭", "topic_img_id": 9, "description": None},
]

IMAGE_SEEDS = [
    (1, '/banner-1a.png'), (2, '/banner-2a.png'), (3, '/banner-3a.png'), (4, '/category-cake.png'),
    (5, '/category-vg.png'), (6, '/category-dryfruit.png'), (7, '/category-fry-a.png'), (8, '/category-tea.png'),
    (9, '/category-rice.png'), (10, '/product-dryfruit@1.png'), (13, '/product-vg@1.png'), (14, '/product-rice@6.png'),
    (16, '/1@theme.png'), (17, '/2@theme.png'), (18, '/3@theme.png'), (19, '/detail-1@1-dryfruit.png'),
    (20, '/detail-2@1-dryfruit.png'), (21, '/detail-3@1-dryfruit.png'), (22, '/detail-4@1-dryfruit.png'),
    (23, '/detail-5@1-dryfruit.png'), (24, '/detail-6@1-dryfruit.png'), (25, '/detail-7@1-dryfruit.png'),
    (26, '/detail-8@1-dryfruit.png'), (27, '/detail-9@1-dryfruit.png'), (28, '/detail-11@1-dryfruit.png'),
    (29, '/detail-10@1-dryfruit.png'), (31, '/product-rice@1.png'), (32, '/product-tea@1.png'),
    (33, '/product-dryfruit@2.png'), (36, '/product-dryfruit@3.png'), (37, '/product-dryfruit@4.png'),
    (38, '/product-dryfruit@5.png'), (39, '/product-dryfruit-a@6.png'), (40, '/product-dryfruit@7.png'),
    (41, '/product-rice@2.png'), (42, '/product-rice@3.png'), (43, '/product-rice@4.png'), (44, '/product-fry@1.png'),
    (45, '/product-fry@2.png'), (46, '/product-fry@3.png'), (47, '/product-tea@2.png'), (48, '/product-tea@3.png'),
    (49, '/1@theme-head.png'), (50, '/2@theme-head.png'), (51, '/3@theme-head.png'), (52, '/product-cake@1.png'),
    (53, '/product-cake@2.png'), (54, '/product-cake-a@3.png'), (55, '/product-cake-a@4.png'), (56, '/product-dryfruit@8.png'),
    (57, '/product-fry@4.png'), (58, '/product-fry@5.png'), (59, '/product-rice@5.png'), (60, '/product-rice@7.png'),
    (62, '/detail-12@1-dryfruit.png'), (63, '/detail-13@1-dryfruit.png'), (65, '/banner-4a.png'), (66, '/product-vg@4.png'),
    (67, '/product-vg@5.png'), (68, '/product-vg@2.png'), (69, '/product-vg@3.png'),
]


def _truncate_tables(tables: Iterable[str]) -> None:
    db.session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    try:
        for table in tables:
            db.session.execute(text(f"TRUNCATE TABLE `{table}`"))
    finally:
        db.session.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def seed_users() -> None:
    _truncate_tables(["identity", "article", "user"])
    user_table = User.__table__
    identity_table = Identity.__table__

    for user in USER_SEEDS:
        db.session.execute(
            user_table.insert().values(
                id=user["id"],
                nickname=user["nickname"],
                auth=user["auth"],
                group_id=user["group_id"],
                avatar=user["avatar"],
                extend=None,
                create_time=user.get("create_time", None),
                update_time=user.get("update_time", None),
                delete_time=user.get("delete_time", None)
            )
        )

    for identity in IDENTITY_SEEDS:
        db.session.execute(
            identity_table.insert().values(
                id=identity["id"],
                user_id=identity["user_id"],
                type=identity["type"],
                identifier=identity["identifier"],
                credential=identity["credential"],
                verified=identity["verified"],
                create_time=identity.get("create_time", None),
                update_time=identity.get("update_time", None),
                delete_time=identity.get("delete_time", None)
            )
        )


def seed_products() -> None:
    _truncate_tables(["product_property", "product_image", "product", "category", "image"])
    image_table = Image.__table__
    category_table = Category.__table__
    product_table = Product.__table__
    product_image_table = Product2Image.__table__
    property_table = Product2Property.__table__

    for img_id, url in IMAGE_SEEDS:
        db.session.execute(image_table.insert().values(id=img_id, url=url, **{"from": 1}))
    for category in CATEGORY_SEEDS:
        db.session.execute(category_table.insert().values(**category))
    for seed in PRODUCT_SEEDS:
        db.session.execute(product_table.insert().values(id=seed["id"], name=seed["name"], price=seed["price"], stock=seed["stock"], category_id=seed["category_id"], main_img_url=seed["main_img_url"], **{"from": 1}, summary=None))
        db.session.execute(product_image_table.insert().values(product_id=seed["id"], img_id=seed["img_id"], order=1))
    for img_id, order in ((20, 2), (21, 3), (22, 4), (23, 5), (24, 6), (25, 7), (26, 8), (27, 9), (29, 10), (28, 11), (62, 12), (63, 13)):
        db.session.execute(product_image_table.insert().values(product_id=11, img_id=img_id, order=order))
    for pid, name, detail, product_id in [(1, '品名', '杨梅', 11), (2, '口味', '青梅味 雪梨味 黄桃味 菠萝味', 11), (3, '产地', '火星', 11), (4, '保质期', '180天', 11), (5, '品名', '梨子', 2), (6, '产地', '金星', 2), (7, '净含量', '100g', 2), (8, '保质期', '10天', 2)]:
        db.session.execute(property_table.insert().values(id=pid, name=name, detail=detail, product_id=product_id))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=("users", "products", "all"), default="all")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        with db.session.begin():
            if args.scope in ("users", "all"):
                seed_users()
            if args.scope in ("products", "all"):
                seed_products()


if __name__ == '__main__':
    main()
