# -*- coding:utf-8 -*-
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator
from goods.models import GoodsKind, GoodsSKU, BannerList, PromotionList, PartitionList
from order.models import ItemsInfo

# Create your views here.


class IndexView(View):
    """首页视图"""
    def get(self, request):
        cache.delete('index_cache')   # 清除缓存
        context = cache.get('index_cache')
        if not context:
            print("设置缓存")
            # 若没有从缓存中获取到用户近期访问的数据，则从数据库查询并获取数据，同时这一次将数据保存到缓存中
            # 获取商品种类信息
            goods_kind = GoodsKind.objects.all().order_by('index')
            # 获取轮播图商品信息
            goods_banner = BannerList.objects.all().order_by('index')     # 图片展示按index升序排序
            # 获取促销活动商品信息
            goods_promotion = PromotionList.objects.all().order_by('index')
            # 获取分区商品信息
            # goods_partition = PartitionList.objects.all()
            print(f'测试0{goods_kind}')
            for kind in goods_kind:
                # 获取分区商品中文字展示信息
                text_dis = PartitionList.objects.filter(foreign_kind=kind, display=0).order_by('index')
                # 获取分区商品中图片展示信息
                image_dis = PartitionList.objects.filter(foreign_kind=kind, display=1).order_by('index')
                # 将上面的属性直接添加给GoodsKind类的kind实例，方便在模板中使用
                kind.text_dis = text_dis
                kind.image_dis = image_dis
                print(f'测试{text_dis, image_dis}')
            context = {'goods_kind': goods_kind, 'goods_banner': goods_banner,
                       'goods_promotion': goods_promotion}
            cache.set('index_cache', context, 3600)

        # 获取购物车商品数目
        nums_in_cart = 0
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection()
            # 存储购物车数据的hash表的name的格式是cart_userID
            # 获取用户购物车中商品数量
            nums_in_cart = conn.hlen(f'cart_{user.id}')
        # 打包信息，方便传入模板中使用
        context['nums_in_cart'] = nums_in_cart
        return render(request, 'index.html', context)


class DetailsView(View):
    """商品详情页"""
    def get(self, request, goods_id):
        # 获取具体商品的id
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))
        print(f'测试库存：{sku.stock, sku.name}')
        # 获取同spu类型的商品信息，提供链接到商品规格选项下面
        skus_of_same_spu = GoodsSKU.objects.filter(foreign_spu=sku.foreign_spu).exclude(id=goods_id)
        # 获取分类栏的信息
        kinds = GoodsKind.objects.all()
        # 获取指定goods_id的商品的评论信息
        print(f'{sku.id}')
        items_info = ItemsInfo.objects.filter(foreign_sku=sku.id).exclude(review='')  # 不需要空评论商品
        print(f'获取非空评商品：{items_info}')
        # 获取（两条）同类型商品作为新品推荐
        new_on_sells = GoodsSKU.objects.filter(foreign_kind=sku.foreign_kind).exclude(id=goods_id).order_by('-create_time')[:2]  # -代表逆序
        # 获取购物车中商品的数目
        nums_in_cart = 0
        user = request.user
        if user.is_authenticated:
            # 获取购物车中商品类数
            conn = get_redis_connection()
            nums_in_cart = conn.hlen(f'cart_{user.id}')
            # 当前访问了某个商品详情页，要删除历史记录中该商品的记录（如果没有什么都不做）
            conn.lrem(f'record_{user.id}', 0, goods_id)
            # 然后从存储历史记录的list的左侧插入该记录
            conn.lpush(f'record_{user.id}', goods_id)
            # # 只保存5条记录
            # conn.ltrim(f'record_{user.id}', 0, 4)
        # print(f'打印所有分类kinds：{kinds}')
        # 打包上下文
        context = {'sku': sku, 'kinds': kinds,
                   'items_info': items_info,
                   'new_on_sells': new_on_sells,
                   'nums_in_cart': nums_in_cart,
                   'skus_of_same_spu': skus_of_same_spu}
        return render(request, 'details.html', context)


class ListView(View):
    """商品列表页/list/kind_id/page?sort=排序id"""
    def get(self, request, kind_id, page):
        # 获取指定kind_id的所有商品对象
        try:
            kind = GoodsKind.objects.get(id=kind_id)
        except GoodsKind.DoseNotExist:
            return redirect(reverse('goods:index'))
        # 获取所有商品种类，用于模板中的下拉栏
        all_kinds = GoodsKind.objects.all()

        # 根据商品种类获取该类所有商品对象
        # 对获取到的商品对象执行排序-->默认or价格or人气（销量）
        sort = request.GET.get('sort')
        if sort == 'hot':
            skus = GoodsSKU.objects.filter(foreign_kind=kind).order_by('-sales_volume')
        elif sort == 'price':
            skus = GoodsSKU.objects.filter(foreign_kind=kind).order_by('price')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(foreign_kind=kind).order_by('id')  # 默认用id排序

        # 对排好序的对象分页
        paginator = Paginator(skus, 1)
        # 用户输入页码防错（在url中已经规定了page必须是int型）（无法输入-1这类会被视为字符串）
        page = min(page, paginator.num_pages)
        skus_in_page = paginator.page(page)     # 包含第page页的所有商品对象（类型为Page）
        # 实现列表页上最多显示5个页码：显示前两页+当前页+后两页
        # 1.总页数小于5：显示所有页
        # 2.页码page<3为前2页，显示前5页
        # 3.页面page为后2页，显示后5页
        # 4.页面page有前两页和后两页，直接显示
        if paginator.num_pages < 5:
            pages = range(1, page+1)
        elif page < 3:
            pages = range(1, 6)
        elif page > paginator.num_pages - 2:
            pages = range(paginator.num_pages-4, paginator.num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 获取（2条）推荐的新品信息和购物车商品数目（同details）
        new_on_sells = GoodsSKU.objects.filter(foreign_kind=kind).order_by('-create_time')[:2]  # -代表逆序
        # 获取购物车中商品的数目
        nums_in_cart = 0
        user = request.user
        if user.is_authenticated:
            # 获取购物车中商品类数
            conn = get_redis_connection()
            nums_in_cart = conn.hlen(f'cart_{user.id}')

        # 根据模板需求组织上下文
        context = {'kind': kind, 'kinds': all_kinds,
                   'skus_in_page': skus_in_page, 'new_on_sells': new_on_sells,
                   'nums_in_cart': nums_in_cart, 'sort': sort, 'pages': pages}
        return render(request, 'list.html', context)

