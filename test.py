# -*- coding:gbk -*-
import re


# # re中(?P...)的用法
# import re
# s = '1102231990xxxxxxxx'
# res = re.search('(?P<province>\d{3})(?P<city>\d{3})(?P<born_year>\d{4})',s)
# print(res.group(), type(res.group()))
# print(res.groupdict())


from itsdangerous import TimedJSONWebSignatureSerializer as Srlz

srlz = Srlz("秘钥测试", 1200)
info = {"confirm": '我是秘钥'}
pswd = srlz.dumps(info)
dcd = pswd.decode()  # decode之前是bytes类，decode之后是str
# print(type(pswd), '\n', pswd, '\n', type(dcd), '\n', dcd)

# 两种获取字典value的方法，get方法没获取到不会报错
# print(info['1'])
# print(info.get('1'))


# token = 123
# username = 'username'
# active = f'http://127.0.0.1/active/{token}'
# message = ''
# html_message = f'<h1>{username}, 欢迎你成为天天生鲜注册会员</h1>请点击下面的链接激活账户：<br/>' \
#                f'<a href="{active}">{active}</a>'
#
# print(html_message)
#
# print(__name__)
# if __name__ == '__main__':
#     print(__name__)


# print(int('0xb2', 16))
#
# import re
# phone = '19286401245 '
# if re.match(r'1[3|4|5|7|8|9][0-9]{9}$', phone):
#     print(True)
# # print(re.match(r'1[3|4|5|7|8|9][0-9]{9}$', phone).group())
#
# al = [1, 2, 3]
# print([i for i in al])
#
# print(sum(i for i in range(5)))
#
# print(b'a'.decode())
# print(b'1'.decode())
# print('a'.encode())


a = '123'
b = '2'
print(a-b)
