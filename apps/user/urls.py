from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from user.views import RegisterView, LoginView, ActivateView, UserAddressView, UserInfoView, UserOrderView, LogoutView


urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),  # 注册
    url(r'^activate/(?P<token>.*)$', ActivateView.as_view(), name='activate'),   # 激活，正则表达式.*可以匹配到token所有字符
    url(r'^login$', LoginView.as_view(), name='login'),    # 登录
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),  # 用户中心-订单
    # url(r'^address$', login_required(UserAddressView.as_view()), name='address'),  # 用户中心-地址
    # url(r'^$', login_required(UserInfoView.as_view()), name='info'),  # 用户中心-信息

    # 编写了专门实现登录验证的方法LoginRequiredMixin(并在视图中继承)，因此可以直接调用as_view()方法
    url(r'^order$', UserOrderView.as_view(), name='order'),  # 用户中心-订单
    url(r'^address$', UserAddressView.as_view(), name='address'),  # 用户中心-地址
    url(r'^$', UserInfoView.as_view(), name='info'),  # 用户中心-信息
]

