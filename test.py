# -*- coding:gbk -*-
import re


# # re��(?P...)���÷�
# import re
# s = '1102231990xxxxxxxx'
# res = re.search('(?P<province>\d{3})(?P<city>\d{3})(?P<born_year>\d{4})',s)
# print(res.group(), type(res.group()))
# print(res.groupdict())


from itsdangerous import TimedJSONWebSignatureSerializer as Srlz

srlz = Srlz("��Կ����", 1200)
info = {"confirm": '������Կ'}
pswd = srlz.dumps(info)
dcd = pswd.decode()  # decode֮ǰ��bytes�࣬decode֮����str
# print(type(pswd), '\n', pswd, '\n', type(dcd), '\n', dcd)

# ���ֻ�ȡ�ֵ�value�ķ�����get����û��ȡ�����ᱨ��
# print(info['1'])
# print(info.get('1'))


# token = 123
# username = 'username'
# active = f'http://127.0.0.1/active/{token}'
# message = ''
# html_message = f'<h1>{username}, ��ӭ���Ϊ��������ע���Ա</h1>������������Ӽ����˻���<br/>' \
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
