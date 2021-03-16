from django.urls import path, include
from cart.views import AddGoodsToCart, MyCart, CartInfoUpdate, CartGoodsDelete

urlpatterns = [
    path('add/', AddGoodsToCart.as_view(), name='add'),     # 添加商品
    path('mycart/', MyCart.as_view(), name='mycart'),    # 我的购物车
    path('update/', CartInfoUpdate.as_view(), name='update'),   # 数量修改后更新
    path('delete/', CartGoodsDelete.as_view(), name='delete'),   # 购物车商品删除
]
