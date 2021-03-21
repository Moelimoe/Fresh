from django.urls import path, include
from order.views import OrderCheckOut, OrderCommit, OrderPay, OrderQuery, OrderReview

urlpatterns = [
    path('checkout/', OrderCheckOut.as_view(), name='checkout'),    # �ύ����
    path('commit/', OrderCommit.as_view(), name='commit'),  # ��������
    path('pay/', OrderPay.as_view(), name='pay'),  # ����֧��
    path('query/', OrderQuery.as_view(), name='query'),  # ֧���ɹ�
    path('review/<str:order_id>', OrderReview.as_view(), name='review'),  # ��������
]
