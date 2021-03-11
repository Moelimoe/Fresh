# -*- coding:utf-8 -*-
from haystack import indexes
from goods.models import GoodsSKU


# 指定对于某个类的某些数据建立索引
class GoodsSKUIndexes(indexes.SearchIndex, indexes.Indexable):
    # 指定索引来自于一个文本类索引文件（会自动路由到按照格式建立的目录下的文件）
    # use_templates=True是指要按照指定的txt文件里的字段进行匹配（txt文件的存放位置固定）
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return GoodsSKU

    # 根据返回的对象建立索引
    def index_queryset(self, using=None):
        return self.get_model().objects.all()
