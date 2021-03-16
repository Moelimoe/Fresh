from django.urls import path, include
from order.views import OrderCheckOut, OrderCommit

urlpatterns = [
    path('checkout/', OrderCheckOut.as_view(), name='checkout'),    # 提交订单
    path('commit/', OrderCommit.as_view(), name='commit'),  # 订单创建
]
