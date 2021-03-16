# -*- coding:utf-8 -*-
from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from utils.Mixin import LoginRequiredMixin
# Create your views here.


class AddGoodsToCart(View):
    def post(self, request):
        # 接收数据
        user = request.user
        if not user.is_authenticated:   # LoginRequiredMixin并不会使未登录者跳转到登录页面，所以在这里判断
            return JsonResponse({'res': 0, 'err_msg': '用户未登录，请先登录'})
        sku_id = request.POST.get('sku_id')
        count = int(request.POST.get('count'))  # 前端输入有确保只能输入整数
        # 校验数据
        # 1.完整性
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'err_msg': '商品信息不完整，请重试'})
        # 当用户直接在浏览器地址栏输入任意数字时要验证数字的合法性

        # # 2.输入的合法性    # 前端输入有确保只能输入整数
        # try:
        #     count = int(count)
        # except ValueError as e:
        #     return JsonResponse({'res': 2, 'err_msg': '输入格式错误'})

        # 3.存在性
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoseNotExist:
            return JsonResponse({'res': 3, 'err_msg': '没有找到相关的商品'})

        # 业务处理
        # 同步变更购物车页面的信息
        conn = get_redis_connection()
        # 判断添加的商品是否已存在于购物车中：用hget获取cart name为cart_商品id的hash表中key为sku_id的值（即商品数目）
        cart_id = f'cart_{user.id}'
        num_in_cart = conn.hget(cart_id, sku_id)
        # # 校验添加是否超库存（在前端已经校验，这里可以不校验）
        # if count > int(sku.stock):
        #     return JsonResponse({'res': 4, 'err_msg': '添加数量超过库存，请重试'})
        if num_in_cart:
            count += int(num_in_cart)
        # 计算购物车中商品数目
        conn.hset(cart_id, sku_id, count)
        total = conn.hlen(cart_id)
        # print(f'获取cart_id:{cart_id}的购物车商品类总数：{total}')
        # 返回数据
        return JsonResponse({'res': 5, 'err_msg': '加入购物车成功', 'total': total})


class MyCart(LoginRequiredMixin, View):
    def get(self, request):
        # 获取数据
        # 获取用户
        user = request.user
        # 连接redis
        conn = get_redis_connection()
        # 根据用户id从redis获取用户的购物车商品信息（字典型{'商品id': '商品数量'}）
        goods_in_cart = conn.hgetall(f'cart_{user.id}')
        skus = []
        total = aggregate_amount = 0
        for sku_id, count in goods_in_cart.items():
            sku = GoodsSKU.objects.get(id=sku_id)  # 根据商品id获取商品的类对象
            # print(f'测试，进入cart遍历')
            count = int(count)      # count是byte类型
            stock = int(sku.stock)
            count = stock if count > stock else count
            # 小计
            amount = round(sku.price*count, 2)
            # 直接给商品增加属性【小计】和【数量】（感觉不太合适啊，sku商品类还要用于其他地方，暂时先这样做）
            sku.amount = amount
            sku.count = count
            skus.append(sku)    # 小计和数量打包到sku
            # 价格合计
            aggregate_amount += amount
            # 计算商品总件数
            total += count

        # # 计算购物车商品总件数(total)也可以用hvals(cart_userid)
        # vals = conn.hvals(f'cart_{user.id}')
        # total = sum(int(v) for v in vals)
        # print(f'总数{total}')

        context = {'skus': skus, 'total': total,
                   'aggregate_amount': round(aggregate_amount, 2)}
        # 在js也要用toFixed(2)，固定小数位，因为还会在前端执行计算

        return render(request, 'cart.html', context)


# /cart/update
class CartInfoUpdate(View):
    def post(self, request):
        # 使用的JsonResponse，要验证一下登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'err_msg': '用户未登录，请先登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验数据
        # 1.完整性
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'err_msg': '商品信息不完整，请重试'})
        # 当用户直接在浏览器地址栏输入任意数字时要验证数字的合法性
        # 2.输入的合法性
        try:
            count = int(count)
        except ValueError as e:
            return JsonResponse({'res': 2, 'err_msg': '输入格式错误'})
        # 3.商品存在性
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoseNotExist:
            return JsonResponse({'res': 3, 'err_msg': '没有找到相关的商品'})

        # 业务处理
        conn = get_redis_connection()
        # 查看数量是否超过库存

        # 前端已实现库存校验，这一段可以不用了
        # if count > int(sku.stock):
        #     return JsonResponse({'res': 4, 'err_msg': '商品库存不足', 'count': count})

        # 更新购物车件数
        conn.hset(f'cart_{user.id}', sku_id, count)

        # 获取用户购物车cart_userid中【总件数】，用一个【list】存储
        vals = conn.hvals(f'cart_{user.id}')
        print(type(vals), vals, '测试')
        total = sum(int(v) for v in vals)
        print(total)
        # 返回应答
        return JsonResponse({'res': 5, 'err_msg': '设置成功', 'total': total})


class CartGoodsDelete(View):
    def post(self, request):
        # 登录验证
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'err_msg': '用户未登录，请先登录'})
        # 接收数据-->要删除的商品id
        sku_id = request.POST.get('sku_id')
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 1, 'err_msg': '要删除的商品不存在'})

        # 处理业务，删除指定商品-->用hdel(cart_id, sku_id)
        conn = get_redis_connection()
        conn.hdel(f'cart_{user.id}', sku_id)
        # 计算购物车商品总件数(total)也可以用hvals(cart_userid)
        vals = conn.hvals(f'cart_{user.id}')
        total = sum(int(v) for v in vals)
        # 返回成功应答
        return JsonResponse({'res': 2, 'msg': '删除成功', 'total': total})

