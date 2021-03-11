# -*- coding:utf-8 -*-
from django.db import models
from db.base_model import BaseModel


class OrderInfo(BaseModel):
    """订单详情"""
    payment_mode = [(1, "微信支付"),
                    (2, "支付宝支付"),
                    (3, "银联支付"),
                    (4, "货到付款")]
    order_status = [(1, "待支付"),
                    (2, "待发货"),
                    (3, "待收货"),
                    (4, "待评价"),
                    (5, "已完成")]

    # 将订单ID设置为主键
    orderID = models.OneToOneField("order.ItemsInfo", max_length=12, primary_key=True, unique=True,
                                   verbose_name="订单ID", on_delete=models.CASCADE)
    addrID = models.ForeignKey("user.Address", max_length=12, verbose_name="地址ID", on_delete=models.CASCADE)
    userID = models.ForeignKey("user.User", max_length=12, verbose_name="用户ID", on_delete=models.CASCADE)
    checkout = models.SmallIntegerField(default=1, verbose_name="支付方式", choices=payment_mode)
    express_fee = models.SmallIntegerField(default=12, verbose_name="快递费用")
    order = models.SmallIntegerField(default=2, verbose_name="订单状态", choices=order_status)
    # 根据实际业务需求，在订单信息这里额外添加总数目和总金额
    total = models.CharField(max_length=12, default=1, verbose_name="总数目")
    aggregate_amount = models.FloatField(verbose_name="总金额")
    # 添加一个分析数据库未能分析到的项目，支付编号
    transaction_code = models.CharField(max_length=128, verbose_name="支付编号")

    class Meta:
        db_table = "OrderInfo"
        verbose_name = "订单信息"
        verbose_name_plural = verbose_name


class ItemsInfo(BaseModel):
    """订单商品信息"""
    order = models.ForeignKey("order.OrderInfo", max_length=12, verbose_name="订单", on_delete=models.CASCADE)  # 对应订单详情（不是订单ID）
    skuID = models.ForeignKey("goods.GoodsSKU", verbose_name="商品SKU", on_delete=models.CASCADE)
    quantity = models.CharField(max_length=12, default=1, verbose_name="商品数量")
    unit_price = models.FloatField(verbose_name="商品单价")
    review = models.CharField(max_length=1024, verbose_name="商品评价", default='')

    class Meta:
        db_table = "ItemsInfo"
        verbose_name = "订单商品信息"
        verbose_name_plural = verbose_name
