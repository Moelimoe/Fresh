import datetime, os
from django.db import transaction
from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse, HttpResponse
from django.views import View
from django_redis import get_redis_connection
from django.conf import settings
from utils.Mixin import LoginRequiredMixin
from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo, ItemsInfo
from alipay import AliPay, ISVAliPay


# Create your views here.


# 提交订单页面
# /order/checkout
class OrderCheckOut(LoginRequiredMixin, View):
    def post(self, request):
        # 接收和加工数据-->数量，单价，小计，总计，地址
        user = request.user
        sku_ids = request.POST.getlist('sku_ids')  # 获取商品id集合

        # 校验数据
        # 确保不是空提交
        if not sku_ids:
            return redirect('cart:mycart')
        conn = get_redis_connection()
        goods_in_cart = conn.hgetall(f'cart_{user.id}')  # {'商品id': '商品数量'}
        # 业务处理
        # 总计数目和金额
        skus = []  # 存放商品对象sku
        total = aggregate_amount = 0
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)  # 根据id从mysql获取商品信息，如果没有获取到会出错
            # 数量，小计
            count = int(goods_in_cart[sku_id.encode()])  # 根据商品id从redis获取对应于购物车中该商品数量，如果没有获取到会出错
            amount = round(count * sku.price, 2)
            # 总计数目和金额
            total += count
            aggregate_amount += amount
            # 定义商品数量和小计，方便前端使用
            sku.count = count
            sku.amount = amount
            skus.append(sku)
        # 获取用户全部收货地址的类对象
        addresses = Address.objects.filter(foreign_user=user.id)
        # 运费这里没有编辑，直接10元，实际业务中要单独建立运费计算表
        exp_charge = 10
        # 实际需要付款
        amount_to_pay = aggregate_amount - exp_charge
        # json中无法直接使用sku的属性，传一个sku_ids的字符串过去
        sku_ids = ','.join(sku_ids)
        # 准备返回应答
        context = {'skus': skus, 'sku_ids': sku_ids, 'total': total, 'aggregate_amount': round(aggregate_amount, 2),
                   'addresses': addresses, 'exp_charge': exp_charge, 'amount_to_pay': round(amount_to_pay, 2)}
        return render(request, 'checkout.html', context)


# /order/commit
# 地址id，支付方式，订单中商品id
# 悲观锁，必须先拿到锁才能执行事务，适合请求数量多的情况，保证不会出错，但是会牺牲一定的效率
class OrderCommit1(View):
    """订单提交后台创建"""

    @transaction.atomic
    def post(self, request):
        # 验证登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'err_msg': '用户未登录，请重新登录！'})
        # 接收数据
        addr_id = request.POST.get('addr_id')
        pay_mode = request.POST.get('pay_mode')
        sku_ids = request.POST.get('sku_ids')
        # 校验数据
        if not all([addr_id, pay_mode, sku_ids]):
            return JsonResponse({'res': 1, 'err_msg': '接收数据不完整！'})
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'err_msg': '无法匹配用户地址！'})
        if int(pay_mode) not in OrderInfo.payment_modes:
            return JsonResponse({'res': 3, 'err_msg': '支付方式不正确！'})
        exp_charge = 10
        total = 0
        aggregate_amount = 0
        # 业务处理
        # 生成订单ID
        order_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # Mysql事务保存点
        savepoint_1 = transaction.savepoint()
        # 向df_order_info添加记录
        try:
            order = OrderInfo.objects.create(order_id=order_id, foreign_address=addr, foreign_user=user,
                                             checkout_mode=pay_mode, exp_charge=exp_charge,
                                             total=total, aggregate_amount=aggregate_amount,
                                             transaction_code='')
            # skus = GoodsSKU.objects.filter(id_in=sku_ids.split(','))
            sku_ids = sku_ids.split(',')
            conn = get_redis_connection()
            for sku_id in sku_ids:
                try:
                    # select_for_update()相当于mysql开启悲观锁select * from goods_sku where id=5 【for update】
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(savepoint_1)
                    return JsonResponse({'res': 4, 'err_msg': '商品id有误！'})
                # 从redis获取商品数目，价格，库存，销量
                count = int(conn.hget(f'cart_{user.id}', sku_id))
                price = sku.price
                stock = int(sku.stock)
                if count > stock:
                    transaction.savepoint_rollback(savepoint_1)
                    return JsonResponse({'res': 6, 'err_msg': f'商品{sku.name}库存不足'})
                sale_volume = int(sku.sales_volume)
                review = ''
                ItemsInfo.objects.create(foreign_order=order, foreign_sku=sku, qty=count, price=price, review=review)
                # 更新库存和销量
                sku.stock = stock - count
                sku.sales_volume = sale_volume - count
                sku.save()
                # 顺便计算订单总商品数和总金额
                total += count
                aggregate_amount += count * price
            # 更新订单信息中的商品总数和总金额
            order.total = round(total, 2)
            order.aggregate_amount = round(aggregate_amount - exp_charge, 2)
            order.save()
        except Exception as e:
            return JsonResponse({'res': 7, 'err_msg': '支付失败，请重试！'})
        # 事务提交
        transaction.savepoint_commit(savepoint_1)
        # 清除购物车对应商品的记录（redis）
        conn.hdel(f'cart_{user.id}', *sku_ids)
        return JsonResponse({'res': 5, 'msg': '支付成功！'})


# 乐观锁，适合请求数量较少（冲突较少，几率不大）的情况
class OrderCommit(View):
    """订单提交后台创建"""

    @transaction.atomic
    def post(self, request):
        # 验证登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'err_msg': '用户未登录，请重新登录！'})
        # 接收数据
        addr_id = request.POST.get('addr_id')
        pay_mode = request.POST.get('pay_mode')
        sku_ids = request.POST.get('sku_ids')
        # 校验数据
        if not all([addr_id, pay_mode, sku_ids]):
            return JsonResponse({'res': 1, 'err_msg': '接收数据不完整！'})
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'err_msg': '无法匹配用户地址！'})
        if int(pay_mode) not in OrderInfo.payment_modes:
            return JsonResponse({'res': 3, 'err_msg': '支付方式不正确！'})
        exp_charge = 10
        total = 0
        aggregate_amount = 0
        # 业务处理
        # 生成订单ID
        order_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # Mysql事务保存点
        savepoint_1 = transaction.savepoint()
        # 向df_order_info添加记录
        try:
            order = OrderInfo.objects.create(order_id=order_id, foreign_address=addr, foreign_user=user,
                                             checkout_mode=pay_mode, exp_charge=exp_charge,
                                             total=total, aggregate_amount=aggregate_amount,
                                             transaction_code='')
            # 向df_items_info添加记录
            # skus = GoodsSKU.objects.filter(id_in=sku_ids.split(','))
            sku_ids = sku_ids.split(',')
            conn = get_redis_connection()
            for sku_id in sku_ids:
                for i in range(3):  # 三次提交机会，如果都失败则认为订单提交失败
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(savepoint_1)
                        return JsonResponse({'res': 4, 'err_msg': '商品id有误！'})
                    # 从redis获取商品数目，价格，库存，销量
                    count = int(conn.hget(f'cart_{user.id}', sku_id))
                    price = sku.price
                    stock = int(sku.stock)
                    if count > stock:
                        transaction.savepoint_rollback(savepoint_1)
                        return JsonResponse({'res': 6, 'err_msg': f'商品{sku.name}库存不足'})
                    sales_volume = int(sku.sales_volume)
                    review = ''
                    # 乐观锁使用，查询时不加锁，等到更新时比对要修改的对象的数据是否还符合要求，符合则更新否则拒绝更新
                    # 计算库存和销量
                    origin_stock = stock
                    new_stock = origin_stock - count
                    new_sales = sales_volume + count
                    # print(f'测试乐观锁库存：{sku.stock},  收件人：{addr.receiver}')
                    # import time
                    # time.sleep(6)  # 测试：不立即返回结果，而是等待另一个用户也提交订单
                    # 更新时限制条件：原来的属性如果【没有变化】则执行更新，否则不更新
                    # 如果查询到的结果是不再符合要求的（被修改），则res接收的是0（修改的字段条数是0）否则res得到的是1
                    # 如果库存没有变更，则更新库存和销量
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                        sales_volume=new_sales)
                    if str(res) == '0':
                        if i == 2:  # for循环尝试第三次提交
                            transaction.rollback(savepoint_1)
                            return JsonResponse({'res': 7, 'err_msg': '支付失败，库存不匹配'})
                        continue
                    # 创建订单的商品信息，需要确定GoodsSKU的update没有失败才执行
                    ItemsInfo.objects.create(foreign_order=order, foreign_sku=sku, qty=count, price=price,
                                             review=review)
                    # 顺便计算订单总商品数和总金额
                    total += count
                    aggregate_amount += count * price
                    break  # 成功时直接跳出for循环
            # 更新订单信息中的商品总数和总金额
            order.total = round(total, 2)
            order.aggregate_amount = round(aggregate_amount - exp_charge, 2)
            order.save()
        except Exception as e:
            return JsonResponse({'res': 7, 'err_msg': f'支付失败，数据提交过程中出了问题{e}，请重试！'})
        # 事务提交
        transaction.savepoint_commit(savepoint_1)
        # 清除购物车对应商品的记录（redis）
        conn.hdel(f'cart_{user.id}', *sku_ids)
        return JsonResponse({'res': 5, 'msg': '支付成功！'})


# 支付视图，前端传递的参数：order_id，传递方式post；需要返回的参数：pay_url
# /order/pay/
class OrderPay(View):
    def post(self, request):
        # 登录验证
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 1, 'err_msg': '用户未登录！'})
        # 接收数据
        order_id = request.POST.get('order_id')
        # 校验数据（没有校验空order_id-->认为下面的try不会取得到结果）
        try:
            order = OrderInfo.objects.get(order_id=order_id, foreign_user=user,
                                          checkout_mode=2, order_status=1)  # 要获取准确的订单（支付宝支付方式）
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'err_msg': '订单不存在（或支付方式不正确，不是alipay）'})

        # 业务处理
        # Alipay接口初始化
        app_private_key_path = settings.BASE_DIR + r'\apps\order\app_private_key.pem'
        # app_private_key_path = os.path.join(settings.BASE_DIR + r'\apps\order', r'alipay_public_key.pem')
        alipay_public_key_path = settings.BASE_DIR + r'\apps\order\alipay_public_key.pem'
        app_private_key_string = open(app_private_key_path).read()
        alipay_public_key_string = open(alipay_public_key_path).read()
        alipay = AliPay(
            appid='2021000117622912',
            app_notify_url='http://127.0.0.1:8000/user/order/1/',
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type='RSA2',
            debug=True,
        )
        # 调用支付宝支付API
        total_amount_to_pay = order.aggregate_amount + order.exp_charge  # 需付金额，float
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=total_amount_to_pay,
            subject=f'FRESH--ORDER CHECKOUT{order_id}',
            return_url='http://127.0.0.1:8000/user/order/1/',
            notify_url='http://127.0.0.1:8000/user/order/1/',
        )  # 内网环境，自己查询订单结果，返回和通知的url默认为None
        # 返回应答，支付url的格式如下
        payment_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'payment_url': payment_url, 'msg': '支付成功'})


# /order/query
class OrderQuery(View):
    """提交订单后自动查询支付结果（内网不支持支付宝发送查询结果），前端ajax post传递参数：order_id"""

    def post(self, request):
        # 登录验证
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 1, 'err_msg': '用户未登录！'})
        # 接收数据
        order_id = request.POST.get('order_id')
        # 校验数据（没有校验空order_id-->认为下面的try不会取得到结果）
        try:
            order = OrderInfo.objects.get(order_id=order_id, foreign_user=user,
                                          checkout_mode=2, order_status=1)  # 要获取准确的订单（支付宝支付方式）
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'err_msg': '订单不存在'})

        # 业务处理
        # Alipay接口初始化
        app_private_key_path = settings.BASE_DIR + r'\apps\order\app_private_key.pem'
        # app_private_key_path = os.path.join(settings.BASE_DIR + r'\apps\order', r'alipay_public_key.pem')
        alipay_public_key_path = settings.BASE_DIR + r'\apps\order\alipay_public_key.pem'
        app_private_key_string = open(app_private_key_path).read()
        alipay_public_key_string = open(alipay_public_key_path).read()
        alipay = AliPay(
            appid='2021000117622912',
            app_notify_url='http://127.0.0.1:8000/user/order/1/',
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type='RSA2',
            debug=True,
        )
        # 调用支付宝查询接口alipay.trade.query，会得到一个响应
        import time
        for i in range(60):
            response = alipay.api_alipay_trade_query(out_trade_no=order_id)
            code = response.get('code')  # 获取相应码code
            trade_status = response.get('trade_status')
            if code == '10000' and trade_status == 'TRADE_SUCCESS':  # 接口调用成功且支付成功
                order.order_status = 4  # 订单状态更改为待评价
                order.save()
                print('支付成功')
                return JsonResponse({'res': 3, 'msg': '支付成功'})
            # 接口调用成功，等待付款中（40004是正在处理交易）
            elif code == '40004' or (code == '10000' and trade_status == 'WAIT_BUYER_PAY'):
                # 每5s重新查询一次，最多5分钟
                print(f'等待支付{i}')
                time.sleep(5)
                continue
            else:
                print(code, '测试code')
                return JsonResponse({'res': 4, 'err_msg': '支付失败'})
        return JsonResponse({'res': 4, 'err_msg': '支付失败，超过支付时间（5分钟）'})


# 订单评价视图/order/review/order_id
# 前端请求方式：post；（点击去评价）参数：order_id，捕获路由中的参数
class OrderReview(View, LoginRequiredMixin):
    def get(self, request, order_id):
        """从订单页进入到评论页"""
        user = request.user
        # 接收数据（直接传递过来了）
        # 校验数据
        try:    # 判断是不是【待评价的订单】，绑定用户和订单id且是待评价，避免非法进入
            order_to_review = OrderInfo.objects.get(order_id=order_id, foreign_user=user, order_status=4)
        except OrderInfo.DoesNotExist:  # 重定向到订单页面
            return redirect(reverse('user:order', args=(1,)))
        # 根据【待评价订单】获取该订单中对应的商品对象
        items = ItemsInfo.objects.filter(foreign_order=order_to_review)
        items_to_review = []
        # 业务处理，订单中分商品的类来显示评论
        for item in items:
            sku = item.foreign_sku
            sku.count = item.qty
            sku.amount = round(item.qty*item.price, 2)
            items_to_review.append(item)
        print(f'测试skus对象{items_to_review}')
        context = {'items_to_review': items_to_review, 'order_to_review': order_to_review}
        # 返回应答
        return render(request, 'order_review.html', context)

    def post(self, request, order_id):
        """评论提交页面，获取订单评论发送到商品详情页面"""
        user = request.user
        # 接收数据
        # 校验数据
        try:    # 判断是不是【待评价的订单】，绑定用户和订单id且订单是待评价，避免非法进入
            order_to_review = OrderInfo.objects.get(order_id=order_id, foreign_user=user, order_status=4)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('user:order', args=(1,)))

        num_reviews = int(request.POST.get('num_reviews'))
        if not num_reviews:  # 没有读取到商品的件数
            print('没有读取到商品的件数')
            return redirect(reverse('user:order', args=(1,)))
        print(f'测试需要评论的条数：{num_reviews}')
        # 业务处理
        # 存储已评价的商品对象
        for i in range(1, num_reviews + 1):  # 获取要评价的商品id和对应的评论内容
            sku_id = request.POST.get(f'sku_{i}')
            content = request.POST.get(f'content_{i}')
            print(f'测试评论商品id和内容：{sku_id}, {content}')
            # 修改对应商品对象（ItemsInfo）的review属性（进入评价内容）
            try:
                item = ItemsInfo.objects.get(foreign_sku=sku_id, foreign_order=order_to_review.order_id)
            except ItemsInfo.DoesNotExist:  # 商品id未获取成功
                print('商品id未获取成功')
                return redirect(reverse('user:order', args=(1,)))
            print(f'准备给{item}存入评论：{content}')
            item.review = content
            item.save()
        order_to_review.order_status = 5
        order_to_review.save()
        # 返回应答，重定向到订单页面（商品可能有很多不方便重定向）
        return redirect(reverse('user:order', args=(1,)))

