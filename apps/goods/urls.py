# -*- coding:utf-8 -*-
from django.conf.urls import url
from django.urls import path, re_path
from goods.views import IndexView, DetailsView, ListView

urlpatterns = [
    # url(r'^index$', IndexView.as_view(), name="index"),  # 首页
    path('', IndexView.as_view(), name="index"),  # 首页
    # url(r'^goods/(?P<goods_id>[0-9]+)$', DetailsView.as_view(), name='details'),  # 详情页
    path('goods/<int:goods_id>/', DetailsView.as_view(), name='details'),  # 商品详情页
    path('list/<int:kind_id>/<int:page>/', ListView.as_view(), name='list'),  # 商品列表页
]
