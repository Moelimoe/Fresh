# -*- coding:gbk -*-
import time
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader, RequestContext

# # # 在任务处理中worker（虚拟机）中的该文件下加入以下注释的代码，实现django的初始化
import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()
from goods.models import GoodsKind, BannerList, PromotionList, PartitionList


app = Celery('celery_tasks.tasks', broker=settings.BROKER)


@app.task
def send_activate_email(e_address, username, token):
    print("进入发送激活邮件过程")
    subject = "欢迎注册天天生鲜"
    activate = f'http://127.0.0.1:8000/user/activate/{token}'
    message = ''
    html_message = f'<h1>{username}, 欢迎你成为天天生鲜注册会员</h1>请点击下面的链接激活账户：<br/>' \
                   f'<a href="{activate}">{activate}</a>'
    _from = settings.EMAIL_FROM
    receivers = [e_address]
    send_mail(subject, message, _from, receivers, html_message=html_message)
    for i in range(5):
        print(f'休眠{i+1}秒')
        time.sleep(1)

@app.task
def generate_static_index_html():
    # 获取商品种类信息
    goods_kind = GoodsKind.objects.all()
    # 获取轮播图商品信息
    goods_banner = BannerList.objects.all().order_by('index')  # 图片展示按index升序排序
    # 获取促销活动商品信息
    goods_promotion = PromotionList.objects.all().order_by('index')
    # 获取分区商品信息
    # goods_partition = PartitionList.objects.all()
    for kind in goods_kind:
        # 获取分区商品中文字展示信息
        text_dis = PartitionList.objects.filter(kind=kind, display=0).order_by('index')
        # 获取分区商品中图片展示信息
        image_dis = PartitionList.objects.filter(kind=kind, display=1).order_by('index')
        # 将上面的属性直接添加给GoodsKind类的kind实例，方便在模板中使用
        kind.text_dis = text_dis
        kind.image_dis = image_dis
    # 获取购物车商品数目
    nums_in_cart = 0
    context = {'goods_kind': goods_kind, 'goods_banner': goods_banner,
               'goods_promotion': goods_promotion,
               'nums_in_cart': nums_in_cart}
    # 获取要渲染的静态模板页面
    # 1.获取模板
    template = loader.get_template('static_index.html')
    # 2.定义模板的上下文（本方法没有传入request参数，这一步省略，可以直接传入字典的context）
    # context = RequestContext(request, context)
    # 3.渲染模板
    static_index_html = template.render(context)
    # 提前设定静态文件存储路径
    staticfiles_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    # 创建静态文件
    with open(staticfiles_path, 'w') as f:
        f.write(static_index_html)
