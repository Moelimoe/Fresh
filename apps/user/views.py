# -*- coding:gbk -*-
import re
import time
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django_redis import get_redis_connection
from django.contrib.auth.decorators import login_required
from itsdangerous import SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

# from django.core.mail import send_mail
from celery_tasks.tasks import send_activate_email
from user.models import User, Address
from goods.models import GoodsSKU
from utils.Mixin import LoginRequiredMixin


# Create your views here.

# ���ص�ע�᷽��
# def register(request):
#     if request.method == 'GET':
#         # ���������ַ���룬����ע��
#         return render(request, 'register.html')
#     else:
#         # ���򣬽��뷽ʽ��POST���ύע����Ϣ����ִ��ע��У��
#         # �� ���ݽ���
#         username = request.POST.get('user_name')  # get�Ķ�����html�Ѷ���
#         password = request.POST.get('pwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#         # �� ������֤
#         # ��֤�����Ƿ�����д
#         if not all([username, password, email]):
#             return render(request, 'register.html', {'errmsg': "���ݲ�����"})
#         # ��֤�Ƿ�ͬ��Э��
#         if allow != 'on':
#             return render(request, 'register.html', {'errmsg': 'ͬ��Э�����ע��'})
#         # ��֤�����ʽ�Ƿ���ȷ
#         if not re.match(r'[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {'errmsg': "�����ʽ����ȷ"})
#         # ʹ��django�Դ��ķ���������User���������ע����û����Ƿ��ظ�
#         try:
#             user = User.objects.get(username, email, password)
#         except User.DoesNotExist:  # ���ûget������ᱨ�����ڵĴ���
#             user = None
#         if not user:
#             return render(request, 'register.html', {'errmsg': "�û����Ѵ���"})
#         # ��ҵ����
#         user = User.objects.create_user(username, email, password)
#         user.is_active = 0
#         user.save()
#         # �ܷ���Ӧ��
#         return redirect(reverse("goods:index"))


# django����ͼViewʵ��ע�᷽��
class RegisterView(View):
    def get(self, request):
        print("get����ֱ�ӷ���ע��ҳ��")
        return render(request, 'register.html')

    def post(self, request):
        # ���뷽ʽ��POST���ύע����Ϣ����ִ��ע��У��
        # �� ���ݽ���
        username = request.POST.get('user_name')  # get�Ķ�����html�Ѷ���
        print(f"������û���Ϊ��{username}")
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # �� ������֤
        # ��֤�����Ƿ�����д
        if not all([username, password, email]):    # allow����ѡ���������ݲ��������������ﲻУ��allow
            print("�û�����ȫ")
            return render(request, 'register.html', {'errmsg': "���ݲ�����"})
        # ��֤�Ƿ�ͬ��Э��
        if allow != 'on':
            print("δͬ��")
            return render(request, 'register.html', {'errmsg': 'ͬ��Э�����ע��'})
        # ��֤�����ʽ�Ƿ���ȷ
        if not re.match(r'[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            print("���䲻��")
            return render(request, 'register.html', {'errmsg': "�����ʽ����ȷ"})
        # ʹ��django�Դ��ķ���������User���������ע����û����Ƿ��ظ�
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:    # û��ִ��DoseNotExist���쳣
            print("�û����Ѵ���")
            return render(request, 'register.html', {'errmsg': "�û����Ѵ���"})
        # ��ҵ����
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # ʵ���ʼ������
        # url�ϵ��û�ID������ʾ
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {"confirm": user.id}
        token = serializer.dumps(info).decode()  # ������ܵõ���token���ֽ���ʽ��decode֮������str

        # �û������˻�ʱ�����ʼ�
        # # ����������ʽ���ͣ���������Ӧ��
        # print('����ʽ����')
        # subject = "��ӭע����������"
        # activate = f'http://127.0.0.1/activate/{token}'
        # message = ''
        # html_message = f'<h1>{username}, ��ӭ���Ϊ��������ע���Ա</h1>������������Ӽ����˻���<br/>' \
        #                f'<a href="{activate}">{activate}</a>'
        # _from = settings.EMAIL_FROM
        # receivers = [email]
        # send_mail(subject, message, _from, receivers, html_message=html_message)

        # ������ʹ��celery�첽����
        print("׼��ʹ��celery�첽�����ʼ�")
        send_activate_email.delay(email, username, token)

        # �ܷ���Ӧ��
        print("׼���ض��򷵻���ҳ")
        return redirect(reverse("goods:index"))


class LoginView(View):
    """��¼ҳ��"""

    def get(self, request):
        print("getʽ�����¼ҳ��")

        # username��checked���ڵ�¼ģ�����û����ͼ�ס��¼��Ĭ��ֵ
        if 'username' in request.COOKIES:  # cookie�д����û���
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username, checked = '', ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """��¼У��"""
        # ��������
        print("post�͵�¼�ύ����")
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')
        # У������
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '���ݲ�����'})

        # ҵ���� + # ����Ӧ��
        user = authenticate(username=username, password=password)
        if user is not None:
            # ��֤ͨ����user��ȡ�ɹ�
            if user.is_active:      # ʹ����django�Դ���authenticateģ�飬�������ж��Ƿ񼤻�Ҫ�޸�Դ�루���޸ģ�
                login(request, user)    # django�Դ���login�������Լ�ס�û��ĵ�¼״̬
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)
                if remember == 'on':
                    # ��ס�û�������cookie
                    response.set_cookie('username', username, max_age=7*24*3600)   # ����cookie��dict��ʽ��
                else:
                    # ����ѡ��ס��ɾ����Ӧ�û���cookie
                    response.delete_cookie('username')
                return response
            else:
                return render(request, 'login.html', {'errmsg': '�û�δ����'})
        else:
            return render(request, 'login.html', {'errmsg': '�û������������'})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


class ActivateView(View):
    """�����ʼ�����ͼ"""
    def get(self, request, token):
        """token�Ǵ��û������url�еõ���"""
        print('token:', token)  # token��urls.py�е�token
        serializer = Serializer(settings.SECRET_KEY, 3600)  # ����settings.py�е���Կ
        try:
            # ע��dumps�����ܣ��Ĺ�����ע����ͼ��ʵ���ˣ�����ַ��ȡ���Ǽ��ܺ�ģ��ڼ�����ͼ����ֻ��Ҫ��loads�����ܣ�
            info = serializer.loads(token)
            userID = info['confirm']
            user = User.objects.get(id=userID)  # ����ָ�����������ݿ�����п�
            user.is_active = 1
            print(f'�û�{user.username}����ɹ�')
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as err:
            """ע�⣺ʵ��ҵ����Ӧ�ò��Ƿ���һ���ַ��������Ƿ���һ��ҳ����ʾ���������ѹ��ڣ����ٷ�һ��������ʼ�"""
            return HttpResponse('���������ѹ���')


# �û�����3ҳ��
# /user
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        default_address_info = Address.objects.get_default_address(user=user)
        conn = get_redis_connection()   # ��ȡredisĬ�ϴ洢���ݿ������
        rct_brs_gids = conn.lrange(f'record_{user.id}', 0, 4)    # ��ȡ��������5����Ʒ��¼�ġ�id��
        # rct_brs_info = GoodsSKU.objects.filter(id__in=rct_brs_gids)     # �����ݿ��л�ȡ���������ݣ���id����ģ�
        # �������¼�������ʱ������
        rct_brs_goods = [GoodsSKU.objects.get(id=c_id) for c_id in rct_brs_gids]
        context = {'page': 'user', 'address_info': default_address_info, 'goods_li': rct_brs_goods}
        print(f'��ӡ��������¼{[i for i in rct_brs_goods]}')
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address
class UserAddressView(LoginRequiredMixin, View):
    def get(self, request, errmsg=''):
        # ����ʽ��ȡĬ�ϵ�ַ
        # try:
        #     address_info = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address_info = None

        # �޸�Manager�������ȡĬ�ϵ�ַ
        default_address_info = Address.objects.get_default_address(user=request.user)
        return render(request, 'user_center_addr.html', {'page': 'address',
                                                         'address_info': default_address_info,
                                                         'errmsg': errmsg})

    def post(self, request):
        # ���������
        receiver = request.POST.get('receiver')
        address = request.POST.get('address')
        postcode = request.POST.get('postcode')
        phone = request.POST.get('phone')
        # ��У������
        if not all([receiver, address, phone]):
            return self.get(request, errmsg='���ݲ�����')
            # return render(request, 'user_center_addr.html', {'page': 'address', 'errmsg': '���ݲ�����'})

        if not re.match(r'1[3|4|5|7|8|9][0-9]{9}$', phone):
            return self.get(request, errmsg='�ֻ������ʽ����ȷ')
            # return render(request, 'user_center_addr.html', {'page': 'address', 'errmsg': '�ֻ������ʽ����ȷ'})

        # ��ҵ����
        user = request.user
        # �ж��û��Ƿ�����Ĭ�ϵ�ַ
        # ����ʽ�ж�Ĭ�ϵ�ַ
        # try:
        #     address_info = Address.objects.get(user=user, is_default=True)
        #     # ��Ĭ�ϵ�ַ
        #     is_default = False
        # except Address.DoesNotExist:
        #     # ��Ĭ�ϵ�ַ
        #     is_default = True
        # �޸�Manager�������ȡĬ�ϵ�ַ
        default_address_info = Address.objects.get_default_address(user=user)
        is_default = False if default_address_info else True
        Address.objects.create(foreign_user=user, receiver=receiver, addr=address, postcode=postcode, phone=phone,
                               is_default=is_default)
        # �ﷵ��Ӧ��
        return redirect(reverse('user:address'))

