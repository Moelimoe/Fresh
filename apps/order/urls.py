from django.urls import path, include
from order.views import OrderCheckOut, OrderCommit, OrderPay, OrderQuery, OrderReview

urlpatterns = [
    path('checkout/', OrderCheckOut.as_view(), name='checkout'),    # 提交订单
    path('commit/', OrderCommit.as_view(), name='commit'),  # 订单创建
    path('pay/', OrderPay.as_view(), name='pay'),  # 订单支付
    path('query/', OrderQuery.as_view(), name='query'),  # 支付成功
    path('review/<str:order_id>', OrderReview.as_view(), name='review'),  # 订单评价
]
