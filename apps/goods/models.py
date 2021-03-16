# -*- coding:utf-8 -*-
from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField


class GoodsKind(BaseModel):
    """商品类型表"""
    kind = models.CharField(max_length=20, verbose_name="类型名")
    logo = models.CharField(max_length=20, verbose_name="类型图标")     # logo用的是雪碧图（CSS sprite），不是image类型
    image = models.ImageField(upload_to='kind', verbose_name="商品图片")
    index = models.SmallIntegerField(default=0, verbose_name="展示顺序")

    class Meta:
        db_table = "goods_kind"
        verbose_name = "商品种类"
        verbose_name_plural = verbose_name

    def __str__(self):  # 使实例化后的类有一个自定义的名称，不影响调用其内的属性和方法
        return self.kind


class GoodsSKU(BaseModel):
    """SKU=Stock Keeping Unit(库存单位)，有具体到产品的capacity描述
    例如：金色 256G iphone11"""
    status = [(0, "上架"), (1, "下架")]
    name = models.CharField(max_length=20, verbose_name="具体商品名")
    intro = models.CharField(default='', max_length=256, verbose_name="商品简介")
    price = models.FloatField(max_length=10, verbose_name="价格")
    unit = models.CharField(max_length=12, verbose_name="单位")
    stock = models.CharField(max_length=12, verbose_name="库存")
    is_on_sale = models.BooleanField(default=True, verbose_name="上架状态", choices=status)
    foreign_kind = models.ForeignKey("goods.GoodsKind", verbose_name="商品种类", on_delete=models.CASCADE)
    foreign_spu = models.ForeignKey("goods.GoodsSPU", verbose_name="商品spu", on_delete=models.CASCADE)

    # 在SKU类单独设置销量和图片属性，方便排序时查看（这是实际中应该是根据需求决定是否要单独设置该属性）
    sales_volume = models.CharField(max_length=20, verbose_name="销量")  # 思考：如果要达到上千就用xxk显示，要怎么做？
    image = models.ImageField(verbose_name="图片简介")

    class Meta:
        db_table = "goods_sku"
        verbose_name = "商品SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsSPU(BaseModel):
    """SPU=Standard Product Unit，是某一个商品的最小【类】（口语中会以这个名字只带某一具体产品），
    如iphone11，SPU范围>SKU范围"""
    spu = models.CharField(max_length=20, verbose_name="商品SPU名称")
    # 使用HTML类型存储详情
    detail = HTMLField(blank=True, verbose_name="商品详情")
    # detail = models.TextField(verbose_name="商品详情")

    class Meta:
        db_table = "goods_spu"
        verbose_name = "商品SPU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.spu


class GoodsImage(BaseModel):
    image = models.ImageField(verbose_name="图片路径", upload_to="goods")   # uploadto参数需是一个相对路径
    foreign_sku = models.ForeignKey("goods.GoodsSKU", verbose_name="商品sku", on_delete=models.CASCADE)

    class Meta:
        db_table = "goods_image"
        verbose_name = "商品图片"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.foreign_sku.name+'图'


# 一下三模型是首页展示
class BannerList(BaseModel):
    """首页轮播商品展示model"""
    # foreign_sku = models.ForeignKey("goods.GoodsSKU", verbose_name="商品sku", on_delete=models.CASCADE)
    # 轮播图应该与SPU关联，显示的也是指定商品类
    # foreign_spu = models.ForeignKey("goods.GoodsSPU", verbose_name="商品spu", on_delete=models.CASCADE)
    foreign_kind = models.ForeignKey("goods.GoodsKind", verbose_name="商品kind", on_delete=models.CASCADE)
    image = models.ImageField(verbose_name="轮播商品图片", upload_to="banner")
    index = models.SmallIntegerField(default=0, verbose_name="展示顺序")    # small和非small有啥区别？small好像是省空间

    class Meta:
        db_table = "banner_list"
        verbose_name = "首页轮播商品表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.foreign_kind.kind+'轮播图'


class PromotionList(BaseModel):
    """首页促销商品展示model"""
    # 定义一个名称，方便识别，也可以用于__str__方法的返回
    activity = models.CharField(verbose_name="活动名称", max_length=20)
    image = models.ImageField(verbose_name="促销商品图", upload_to="banner")
    url = models.CharField(verbose_name="活动链接", max_length=256)
    index = models.SmallIntegerField(verbose_name="活动展示顺序", default=0)

    class Meta:
        db_table = "promotion_list"
        verbose_name = "首页促销商品表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.activity


class PartitionList(BaseModel):
    """首页商品分区model"""
    display_choices = ((0, "文字"), (1, "图片"))
    display = models.SmallIntegerField(default=1, choices=display_choices, verbose_name="展示类型")
    foreign_sku = models.ForeignKey("goods.GoodsSKU", verbose_name="商品sku", on_delete=models.CASCADE)
    foreign_kind = models.ForeignKey("goods.GoodsKind", verbose_name="商品kind", on_delete=models.CASCADE)
    index = models.SmallIntegerField(verbose_name="展示顺序", default=0)

    class Meta:
        db_table = 'partition_list'
        verbose_name = "首页商品分区表"
        verbose_name_plural = verbose_name


