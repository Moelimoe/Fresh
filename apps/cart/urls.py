from django.urls import path, include
from cart.views import AddGoodsToCart, MyCart

urlpatterns = [
    path('add/', AddGoodsToCart.as_view(), name='add'),     # 添加商品
    path('mycart/', MyCart.as_view(), name='mycart')    # 我的购物车
]
