# -*- coding:gbk -*-
# import test
# from itsdangerous import TimedJSONWebSignatureSerializer as Srlz
#
# srlz = Srlz("秘钥测试", 1200)
# get_info = srlz.loads(test.pswd)  # loads对象是dumps之后的info，可以decode也可以不decode
# print(get_info['confirm'])
#
# print(isinstance('a', str))
#
# a, b = divmod(12, 10)
# a, b = divmod(7, 10)
# print(a, b)
#
# dic = {'a': 1}
# # dic = {'a':1, 'b':3}
# dic['b'] = 2
# print(dic)
#
# li = [1, 2, 3]
# for i in range(len(li) - 1, -1, -1):
#     print(i, li[i])
#
# a = 0
#
# print((3.14 + 1e20) - 1e20)
# print(3.14 + (1e20 - 1e20))
# print(1e20)
# topic, form = 1, 2
# print({'topics': topic, 'form': form} == {'topic': topic, 'form': form})
#
# res = [[2], [3, 4]]
# for i in range(len(res)):
#     if i % 2 != 0:
#         res[i].reverse()
# print(res)
#
# QUE = []
# print(QUE == [])
# from collections import  deque
# q = deque([1, 2])
# print(q, list(q))

# a = 1
# b = 1.0
# print(a+b)


# ★__str__
class Test:
    def __init__(self):
        self.name = 'test'
        self.any = 'any'

    # def __str__(self):  # 定义str方法只是会使实例化后的类有一个自定义的名字，还可以直接调用实例的属性
    #     return self.name


T = Test()
print(T.any)
print(T)

# re匹配，范围内数字
import re

import datetime
print(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))



