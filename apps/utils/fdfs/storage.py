# -*- coding:gbk -*-
from django.core.files.storage import Storage
from dailyfresh import settings
# from django.conf import settings
from fdfs_client.client import Fdfs_client, get_tracker_conf


class FDFSStorage(Storage):
    def __init__(self, fdfs_url=None, conf_path=None):
        self.fdfs_url = settings.FastDFS_URL if not fdfs_url else fdfs_url
        self.conf_path = settings.CONF_PATH if not conf_path else conf_path

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        """上传（保存）文件"""
        # 指定配置文件
        # tracker_path = get_tracker_conf('./utils/fdfs/client.conf')
        tracker_path = get_tracker_conf(self.conf_path)
        client = Fdfs_client(tracker_path)
        # 上传文件到fdfs服务器，并接受一个fdfs服务器返回的File对象（字典型）
        receive = client.upload_by_buffer(content.read())
        # {'Group name': 'group1',
        # 'Remote file_id': 'group1/M00/00/00/wKgrY2A4Ty2AVr7cAAPYbeRSiPo554.jpg',
        #  'Status': 'Upload successed.',
        #  'Local file name': '/home/image/Desktop/miku1.jpg',
        #  'Uploaded size': '246.00KB',
        #  'Storage IP': '192.168.43.99'}
        if receive.get('Status') != 'Upload successed.':
            raise Exception('文件上传fdfs服务器失败')
        # 修改返回对象：返回文件ID而不是File对象，浏览器接受时，会根据IP和文件ID渲染该地址的图片
        fileid = receive.get('Remote file_id').decode()
        return fileid

    def exists(self, name):
        pass

    def url(self, name):
        """name 就是前面_save()中返回的文件ID"""
        # print('打印测试', settings.FastDFS_URL)
        # return 'http://192.168.43.99:8888/'+name
        return self.fdfs_url+name


