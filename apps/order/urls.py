from django.urls import path, include
from order.views import OrderCheckOut, OrderCommit

urlpatterns = [
    path('checkout/', OrderCheckOut.as_view(), name='checkout'),    # �ύ����
    path('commit/', OrderCommit.as_view(), name='commit'),  # ��������
]
