# -*- coding:utf-8 -*-
from django.db import models
from db.base_model import BaseModel


class OrderInfo(BaseModel):
    """订单详情"""

    CHECKOUT_MODES = [(1, "微信支付"),
                      (2, "支付宝支付"),
                      (3, "银联支付"),
                      (4, "货到付款")]
    ORDER_STATUS = [(1, "待支付"),
                    (2, "待发货"),
                    (3, "待收货"),
                    (4, "待评价"),
                    (5, "已完成")]
    status_choices = {1: "待支付",
                      2: "待发货",
                      3: "待收货",
                      4: "待评价",
                      5: "已完成"}
    # 用于单独判断支付方式的正确性
    payment_modes = {1: "微信支付",
                     2: "支付宝支付",
                     3: "银联支付",
                     4: "货到付款"}
    # 将订单ID设置为主键
    order_id = models.CharField(max_length=128, primary_key=True, unique=True, verbose_name="订单ID")
    foreign_address = models.ForeignKey("user.Address", max_length=12, verbose_name="地址", on_delete=models.CASCADE)
    foreign_user = models.ForeignKey("user.User", max_length=12, verbose_name="所属用户", on_delete=models.CASCADE)
    checkout_mode = models.SmallIntegerField(default=1, verbose_name="支付方式", choices=CHECKOUT_MODES)
    exp_charge = models.SmallIntegerField(default=10, verbose_name="快递费用")
    order_status = models.SmallIntegerField(default=1, verbose_name="订单状态", choices=ORDER_STATUS)
    # 根据实际业务需求，在订单信息这里额外添加总数目和总金额
    total = models.SmallIntegerField(verbose_name="总数目")
    aggregate_amount = models.FloatField(max_length=9, verbose_name="总金额")
    # 添加一个分析数据库未能分析到的项目，支付编号
    transaction_code = models.CharField(max_length=128, default='', verbose_name="支付编号")

    class Meta:
        db_table = "OrderInfo"
        verbose_name = "订单信息"
        verbose_name_plural = verbose_name


class ItemsInfo(BaseModel):
    """订单商品信息（一件）"""
    foreign_order = models.ForeignKey("order.OrderInfo", max_length=12, verbose_name="订单",
                                      on_delete=models.CASCADE)  # 对应订单详情（不是订单ID）
    foreign_sku = models.ForeignKey("goods.GoodsSKU", verbose_name="商品SKU", on_delete=models.CASCADE)
    qty = models.SmallIntegerField(verbose_name="商品数量")
    price = models.FloatField(max_length=9, default=0, verbose_name="商品单价")
    review = models.CharField(max_length=1024, verbose_name="商品评价", default='')

    class Meta:
        db_table = "ItemsInfo"
        verbose_name = "订单商品信息"
        verbose_name_plural = verbose_name
