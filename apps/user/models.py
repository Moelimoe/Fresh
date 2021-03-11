# -*- coding:gbk -*-
from django.contrib.auth.models import AbstractUser
from django.db import models
# from itsdangerous import TimedJSONWebSignatureSerializer as srlz
# from django.conf import settings
from db.base_model import BaseModel


class User(AbstractUser, BaseModel):
    """�û�ģ���࣬AbstractUser��django�Դ����û���Ϣ�࣬�������û�������������ԣ�
    BaseModel���Զ����һ������"""

    # def generate_active_token(self):
    #     """�����û�ǩ���ַ���������"""
    #     serializer = srlz(settings.SECRET_KEY, 3600)
    #     info = {"confirm": self.id}
    #     token = serializer.dump(info)
    #     return token.decode()

    class Meta:
        db_table = "df_user"    # ���ݿ������
        verbose_name = "�û�"
        verbose_name_plural = verbose_name   # ���ֲ����ָ���


class AddressManager(models.Manager):
    def get_default_address(self, user):
        print('self.model:', self.model)
        try:
            # self.model�������Ի�ȡself��������Ӧ��ģ���࣬self����AddressManager��һ��ʵ����Ҳ��Address�е�objects
            address_info = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:  # self.model -> ��objects���ڵ���->��Address
            address_info = None
        return address_info


class Address(BaseModel):
    """��ַ��ģ��"""
    # ע��on_delete����ɾ����������ɾ��ʱ������������Ҳ��ɾ��
    user = models.ForeignKey("user.User", verbose_name="�����˻�", on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20, verbose_name="�ռ���")
    addr = models.CharField(max_length=256, verbose_name="�ջ���ַ")
    postcode = models.CharField(max_length=6, null=True, verbose_name="��������")
    phone = models.CharField(max_length=11, verbose_name="��ϵ�绰")
    is_default = models.BooleanField(default=False, verbose_name="�Ƿ�Ĭ��")

    objects = AddressManager()

    class Meta:
        db_table = "df_address"
        verbose_name = "�ջ���ַ"
        verbose_name_plural = verbose_name




