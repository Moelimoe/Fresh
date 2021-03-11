from django.contrib import admin
from goods.models import GoodsKind, GoodsSKU, GoodsSPU, GoodsImage, BannerList, PromotionList, PartitionList
from celery_tasks.tasks import generate_static_index_html

# Register your models here.


# class BaseModelAdmin(admin.ModelAdmin):
#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)
#         # ��̨�������ݺ������ɾ�̬ҳ��
#         generate_static_index_html.delay()
#
#     def delete_model(self, request, obj):
#         super().delete_model(request, obj)
#         # ��̨ɾ�����ݺ������ɾ�̬ҳ��
#         generate_static_index_html.delay()
#
#
# class GoodsKindAdmin(BaseModelAdmin):
#     pass
# ע�����¾�̬ҳ��ͻ������ݵ�ʵ�ֶ���admin.ModelAdminԴ����save_model��delete_model���޸�ʵ����

admin.site.register(GoodsKind)
admin.site.register(GoodsSKU)
admin.site.register(GoodsSPU)
admin.site.register(GoodsImage)
admin.site.register(BannerList)
admin.site.register(PromotionList)
admin.site.register(PartitionList)

