# -*- coding:gbk -*-
from django.contrib.auth.models import AbstractUser
from django.db import models
# from itsdangerous import TimedJSONWebSignatureSerializer as srlz
# from django.conf import settings
from db.base_model import BaseModel


class User(AbstractUser, BaseModel):
    """用户模型类，AbstractUser是django自带的用户信息类，定义了用户名、密码等属性；
    BaseModel是自定义的一个基类"""

    # def generate_active_token(self):
    #     """生成用户签名字符串（？）"""
    #     serializer = srlz(settings.SECRET_KEY, 3600)
    #     info = {"confirm": self.id}
    #     token = serializer.dump(info)
    #     return token.decode()

    class Meta:
        db_table = "df_user"    # 数据库表项名
        verbose_name = "用户"
        verbose_name_plural = verbose_name   # 汉字不区分复数


class AddressManager(models.Manager):
    def get_default_address(self, user):
        print('self.model:', self.model)
        try:
            # self.model方法可以获取self对象所对应的模型类，self即是AddressManager的一个实例，也即Address中的objects
            address_info = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:  # self.model -> 即objects所在的类->即Address
            address_info = None
        return address_info


class Address(BaseModel):
    """地址类模型"""
    # 注：on_delete级联删除：当主键删除时，相关联的外键也会删除
    user = models.ForeignKey("user.User", verbose_name="所属账户", on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20, verbose_name="收件人")
    addr = models.CharField(max_length=256, verbose_name="收货地址")
    postcode = models.CharField(max_length=6, null=True, verbose_name="邮政编码")
    phone = models.CharField(max_length=11, verbose_name="联系电话")
    is_default = models.BooleanField(default=False, verbose_name="是否默认")

    objects = AddressManager()

    class Meta:
        db_table = "df_address"
        verbose_name = "收货地址"
        verbose_name_plural = verbose_name




