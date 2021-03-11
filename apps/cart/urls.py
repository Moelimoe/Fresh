from django.urls import path, include
from cart.views import AddGoodsToCart, MyCart

urlpatterns = [
    path('add/', AddGoodsToCart.as_view(), name='add'),     # �����Ʒ
    path('mycart/', MyCart.as_view(), name='mycart')    # �ҵĹ��ﳵ
]
