import datetime
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection
from utils.Mixin import LoginRequiredMixin
from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo, ItemsInfo


# Create your views here.


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
        paying_amount = aggregate_amount - exp_charge
        # json中无法直接使用sku的属性，传一个sku_ids的字符串过去
        sku_ids = ','.join(sku_ids)
        print(f'测试skuids:{sku_ids}')
        # 准备返回应答
        context = {'skus': skus, 'sku_ids': sku_ids, 'total': total, 'aggregate_amount': aggregate_amount,
                   'addresses': addresses, 'exp_charge': exp_charge, 'paying_amount': paying_amount}
        return render(request, 'checkout.html', context)


# /order/commit
# 地址id，支付方式，订单中商品id
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
        if pay_mode not in OrderInfo.pay_modes:
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
                import time
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


# 乐观锁
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
        if pay_mode not in OrderInfo.pay_modes:
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
                import time
                for i in range(10):  # 三次提交机会，如果都失败则认为订单提交失败
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
                    ItemsInfo.objects.create(foreign_order=order, foreign_sku=sku, qty=count, price=price,
                                             review=review)

                    # 乐观锁使用，查询时不加锁，等到更新时比对要修改的对象的数据是否还符合要求
                    # 更新库存和销量
                    print('update1')
                    origin_stock = stock
                    new_stock = origin_stock - count
                    new_sales = sales_volume + count
                    print(f'测试乐观锁库存：{sku.stock},  收件人：{addr.receiver}')
                    time.sleep(6)  # 测试：不立即返回结果，而是等待另一个用户也提交订单
                    # 更新时限制条件，
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                        sales_volume=new_sales)
                    print(res)
                    # 如果查询到的结果是不再符合要求的，则res返回的是0（修改的字段条数是0）
                    if str(res) == '0':
                        print('update2')
                        if i == 2:  # 尝试第三次提交
                            transaction.rollback(savepoint_1)
                            return JsonResponse({'res': 7, 'err_msg': '支付失败，库存不匹配'})
                        continue
                    # 顺便计算订单总商品数和总金额
                    total += count
                    aggregate_amount += count * price
                    print('update3')
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
