from django.urls import path, include
from cart.views import AddGoodsToCart, MyCart, CartInfoUpdate, CartGoodsDelete

urlpatterns = [
    path('add/', AddGoodsToCart.as_view(), name='add'),     # �����Ʒ
    path('mycart/', MyCart.as_view(), name='mycart'),    # �ҵĹ��ﳵ
    path('update/', CartInfoUpdate.as_view(), name='update'),   # �����޸ĺ����
    path('delete/', CartGoodsDelete.as_view(), name='delete'),   # ���ﳵ��Ʒɾ��
]
