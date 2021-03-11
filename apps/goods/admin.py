from django.contrib import admin
from goods.models import GoodsKind, GoodsSKU, GoodsSPU, GoodsImage, BannerList, PromotionList, PartitionList
from celery_tasks.tasks import generate_static_index_html

# Register your models here.


# class BaseModelAdmin(admin.ModelAdmin):
#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)
#         # 后台保存数据后重生成静态页面
#         generate_static_index_html.delay()
#
#     def delete_model(self, request, obj):
#         super().delete_model(request, obj)
#         # 后台删除数据后重生成静态页面
#         generate_static_index_html.delay()
#
#
# class GoodsKindAdmin(BaseModelAdmin):
#     pass
# 注：更新静态页面和缓存数据的实现都在admin.ModelAdmin源码中save_model和delete_model中修改实现了

admin.site.register(GoodsKind)
admin.site.register(GoodsSKU)
admin.site.register(GoodsSPU)
admin.site.register(GoodsImage)
admin.site.register(BannerList)
admin.site.register(PromotionList)
admin.site.register(PartitionList)

