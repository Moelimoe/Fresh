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

# 朴素的注册方法
# def register(request):
#     if request.method == 'GET':
#         # 如果输入网址进入，就是注册
#         return render(request, 'register.html')
#     else:
#         # 否则，进入方式是POST，提交注册信息，则执行注册校验
#         # ① 数据接收
#         username = request.POST.get('user_name')  # get的对象在html已定义
#         password = request.POST.get('pwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#         # ② 数据验证
#         # 验证数据是否都有填写
#         if not all([username, password, email]):
#             return render(request, 'register.html', {'errmsg': "数据不完整"})
#         # 验证是否同意协议
#         if allow != 'on':
#             return render(request, 'register.html', {'errmsg': '同意协议才能注册'})
#         # 验证邮箱格式是否正确
#         if not re.match(r'[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {'errmsg': "邮箱格式不正确"})
#         # 使用django自带的方法（导入User方法）检测注册的用户名是否重复
#         try:
#             user = User.objects.get(username, email, password)
#         except User.DoesNotExist:  # 如果没get到，则会报不存在的错误
#             user = None
#         if not user:
#             return render(request, 'register.html', {'errmsg': "用户名已存在"})
#         # ③业务处理
#         user = User.objects.create_user(username, email, password)
#         user.is_active = 0
#         user.save()
#         # ④返回应答
#         return redirect(reverse("goods:index"))


# django类视图View实现注册方法
class RegisterView(View):
    def get(self, request):
        print("get请求，直接返回注册页面")
        return render(request, 'register.html')

    def post(self, request):
        # 进入方式是POST，提交注册信息，则执行注册校验
        # ① 数据接收
        username = request.POST.get('user_name')  # get的对象在html已定义
        print(f"传入的用户名为：{username}")
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # ② 数据验证
        # 验证数据是否都有填写
        if not all([username, password, email]):    # allow不勾选不属于数据不完整，所以这里不校验allow
            print("用户名不全")
            return render(request, 'register.html', {'errmsg': "数据不完整"})
        # 验证是否同意协议
        if allow != 'on':
            print("未同意")
            return render(request, 'register.html', {'errmsg': '同意协议才能注册'})
        # 验证邮箱格式是否正确
        if not re.match(r'[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            print("邮箱不对")
            return render(request, 'register.html', {'errmsg': "邮箱格式不正确"})
        # 使用django自带的方法（导入User方法）检测注册的用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:    # 没有执行DoseNotExist的异常
            print("用户名已存在")
            return render(request, 'register.html', {'errmsg': "用户名已存在"})
        # ③业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 实现邮件激活处理
        # url上的用户ID加密显示
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {"confirm": user.id}
        token = serializer.dumps(info).decode()  # 这里加密得到的token是字节形式，decode之后变成了str

        # 用户激活账户时发送邮件
        # # 方法①朴素式发送（会阻塞响应）
        # print('朴素式发送')
        # subject = "欢迎注册天天生鲜"
        # activate = f'http://127.0.0.1/activate/{token}'
        # message = ''
        # html_message = f'<h1>{username}, 欢迎你成为天天生鲜注册会员</h1>请点击下面的链接激活账户：<br/>' \
        #                f'<a href="{activate}">{activate}</a>'
        # _from = settings.EMAIL_FROM
        # receivers = [email]
        # send_mail(subject, message, _from, receivers, html_message=html_message)

        # 方法②使用celery异步发送
        print("准备使用celery异步发送邮件")
        send_activate_email.delay(email, username, token)

        # ④返回应答
        print("准备重定向返回主页")
        return redirect(reverse("goods:index"))


class LoginView(View):
    """登录页面"""

    def get(self, request):
        print("get式进入登录页面")

        # username和checked用于登录模板中用户名和记住登录的默认值
        if 'username' in request.COOKIES:  # cookie中存有用户名
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username, checked = '', ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录校验"""
        # 接收数据
        print("post型登录提交数据")
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')
        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理 + # 返回应答
        user = authenticate(username=username, password=password)
        if user is not None:
            # 认证通过，user获取成功
            if user.is_active:      # 使用了django自带的authenticate模块，欲单独判断是否激活要修改源码（已修改）
                login(request, user)    # django自带的login方法可以记住用户的登录状态
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)
                if remember == 'on':
                    # 记住用户，设置cookie
                    response.set_cookie('username', username, max_age=7*24*3600)   # 设置cookie（dict形式）
                else:
                    # 不勾选记住，删除对应用户的cookie
                    response.delete_cookie('username')
                return response
            else:
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


class ActivateView(View):
    """激活邮件的视图"""
    def get(self, request, token):
        """token是从用户输入的url中得到的"""
        print('token:', token)  # token是urls.py中的token
        serializer = Serializer(settings.SECRET_KEY, 3600)  # 借用settings.py中的秘钥
        try:
            # 注：dumps（加密）的过程在注册视图中实现了，从网址获取的是加密后的，在激活视图这里只需要再loads（解密）
            info = serializer.loads(token)
            userID = info['confirm']
            user = User.objects.get(id=userID)  # 参数指定可以在数据库表条中看
            user.is_active = 1
            print(f'用户{user.username}激活成功')
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as err:
            """注意：实际业务上应该不是返回一个字符串，而是返回一个页面提示激活链接已过期，并再发一个激活的邮件"""
            return HttpResponse('激活链接已过期')


# 用户中心3页面
# /user
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        default_address_info = Address.objects.get_default_address(user=user)
        conn = get_redis_connection()   # 获取redis默认存储数据库的数据
        rct_brs_gids = conn.lrange(f'record_{user.id}', 0, 4)    # 获取最近浏览的5个商品记录的【id】
        # rct_brs_info = GoodsSKU.objects.filter(id__in=rct_brs_gids)     # 从数据库中获取最近浏览数据（按id排序的）
        # 将浏览记录按照浏览时间排序
        rct_brs_goods = [GoodsSKU.objects.get(id=c_id) for c_id in rct_brs_gids]
        context = {'page': 'user', 'address_info': default_address_info, 'goods_li': rct_brs_goods}
        print(f'打印最近浏览记录{[i for i in rct_brs_goods]}')
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address
class UserAddressView(LoginRequiredMixin, View):
    def get(self, request, errmsg=''):
        # 朴素式获取默认地址
        # try:
        #     address_info = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address_info = None

        # 修改Manager方法后获取默认地址
        default_address_info = Address.objects.get_default_address(user=request.user)
        return render(request, 'user_center_addr.html', {'page': 'address',
                                                         'address_info': default_address_info,
                                                         'errmsg': errmsg})

    def post(self, request):
        # ★接收数据
        receiver = request.POST.get('receiver')
        address = request.POST.get('address')
        postcode = request.POST.get('postcode')
        phone = request.POST.get('phone')
        # ★校验数据
        if not all([receiver, address, phone]):
            return self.get(request, errmsg='数据不完整')
            # return render(request, 'user_center_addr.html', {'page': 'address', 'errmsg': '数据不完整'})

        if not re.match(r'1[3|4|5|7|8|9][0-9]{9}$', phone):
            return self.get(request, errmsg='手机号码格式不正确')
            # return render(request, 'user_center_addr.html', {'page': 'address', 'errmsg': '手机号码格式不正确'})

        # ★业务处理
        user = request.user
        # 判断用户是否已有默认地址
        # 朴素式判断默认地址
        # try:
        #     address_info = Address.objects.get(user=user, is_default=True)
        #     # 有默认地址
        #     is_default = False
        # except Address.DoesNotExist:
        #     # 无默认地址
        #     is_default = True
        # 修改Manager方法后获取默认地址
        default_address_info = Address.objects.get_default_address(user=user)
        is_default = False if default_address_info else True
        Address.objects.create(foreign_user=user, receiver=receiver, addr=address, postcode=postcode, phone=phone,
                               is_default=is_default)
        # ★返回应答
        return redirect(reverse('user:address'))

