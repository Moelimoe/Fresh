# -*- coding:gbk -*-
import time
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader, RequestContext

# # # ����������worker����������еĸ��ļ��¼�������ע�͵Ĵ��룬ʵ��django�ĳ�ʼ��
import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()
from goods.models import GoodsKind, BannerList, PromotionList, PartitionList


app = Celery('celery_tasks.tasks', broker=settings.BROKER)


@app.task
def send_activate_email(e_address, username, token):
    print("���뷢�ͼ����ʼ�����")
    subject = "��ӭע����������"
    activate = f'http://127.0.0.1:8000/user/activate/{token}'
    message = ''
    html_message = f'<h1>{username}, ��ӭ���Ϊ��������ע���Ա</h1>������������Ӽ����˻���<br/>' \
                   f'<a href="{activate}">{activate}</a>'
    _from = settings.EMAIL_FROM
    receivers = [e_address]
    send_mail(subject, message, _from, receivers, html_message=html_message)
    for i in range(5):
        print(f'����{i+1}��')
        time.sleep(1)

@app.task
def generate_static_index_html():
    # ��ȡ��Ʒ������Ϣ
    goods_kind = GoodsKind.objects.all()
    # ��ȡ�ֲ�ͼ��Ʒ��Ϣ
    goods_banner = BannerList.objects.all().order_by('index')  # ͼƬչʾ��index��������
    # ��ȡ�������Ʒ��Ϣ
    goods_promotion = PromotionList.objects.all().order_by('index')
    # ��ȡ������Ʒ��Ϣ
    # goods_partition = PartitionList.objects.all()
    for kind in goods_kind:
        # ��ȡ������Ʒ������չʾ��Ϣ
        text_dis = PartitionList.objects.filter(kind=kind, display=0).order_by('index')
        # ��ȡ������Ʒ��ͼƬչʾ��Ϣ
        image_dis = PartitionList.objects.filter(kind=kind, display=1).order_by('index')
        # �����������ֱ����Ӹ�GoodsKind���kindʵ����������ģ����ʹ��
        kind.text_dis = text_dis
        kind.image_dis = image_dis
    # ��ȡ���ﳵ��Ʒ��Ŀ
    nums_in_cart = 0
    context = {'goods_kind': goods_kind, 'goods_banner': goods_banner,
               'goods_promotion': goods_promotion,
               'nums_in_cart': nums_in_cart}
    # ��ȡҪ��Ⱦ�ľ�̬ģ��ҳ��
    # 1.��ȡģ��
    template = loader.get_template('static_index.html')
    # 2.����ģ��������ģ�������û�д���request��������һ��ʡ�ԣ�����ֱ�Ӵ����ֵ��context��
    # context = RequestContext(request, context)
    # 3.��Ⱦģ��
    static_index_html = template.render(context)
    # ��ǰ�趨��̬�ļ��洢·��
    staticfiles_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    # ������̬�ļ�
    with open(staticfiles_path, 'w') as f:
        f.write(static_index_html)
