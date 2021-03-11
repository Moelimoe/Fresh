from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from user.views import RegisterView, LoginView, ActivateView, UserAddressView, UserInfoView, UserOrderView, LogoutView


urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),  # ע��
    url(r'^activate/(?P<token>.*)$', ActivateView.as_view(), name='activate'),   # ���������ʽ.*����ƥ�䵽token�����ַ�
    url(r'^login$', LoginView.as_view(), name='login'),    # ��¼
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),  # �û�����-����
    # url(r'^address$', login_required(UserAddressView.as_view()), name='address'),  # �û�����-��ַ
    # url(r'^$', login_required(UserInfoView.as_view()), name='info'),  # �û�����-��Ϣ

    # ��д��ר��ʵ�ֵ�¼��֤�ķ���LoginRequiredMixin(������ͼ�м̳�)����˿���ֱ�ӵ���as_view()����
    url(r'^order$', UserOrderView.as_view(), name='order'),  # �û�����-����
    url(r'^address$', UserAddressView.as_view(), name='address'),  # �û�����-��ַ
    url(r'^$', UserInfoView.as_view(), name='info'),  # �û�����-��Ϣ
]

