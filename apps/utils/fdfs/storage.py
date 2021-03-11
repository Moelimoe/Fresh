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
        """�ϴ������棩�ļ�"""
        # ָ�������ļ�
        # tracker_path = get_tracker_conf('./utils/fdfs/client.conf')
        tracker_path = get_tracker_conf(self.conf_path)
        client = Fdfs_client(tracker_path)
        # �ϴ��ļ���fdfs��������������һ��fdfs���������ص�File�����ֵ��ͣ�
        receive = client.upload_by_buffer(content.read())
        # {'Group name': 'group1',
        # 'Remote file_id': 'group1/M00/00/00/wKgrY2A4Ty2AVr7cAAPYbeRSiPo554.jpg',
        #  'Status': 'Upload successed.',
        #  'Local file name': '/home/image/Desktop/miku1.jpg',
        #  'Uploaded size': '246.00KB',
        #  'Storage IP': '192.168.43.99'}
        if receive.get('Status') != 'Upload successed.':
            raise Exception('�ļ��ϴ�fdfs������ʧ��')
        # �޸ķ��ض��󣺷����ļ�ID������File�������������ʱ�������IP���ļ�ID��Ⱦ�õ�ַ��ͼƬ
        fileid = receive.get('Remote file_id').decode()
        return fileid

    def exists(self, name):
        pass

    def url(self, name):
        """name ����ǰ��_save()�з��ص��ļ�ID"""
        # print('��ӡ����', settings.FastDFS_URL)
        # return 'http://192.168.43.99:8888/'+name
        return self.fdfs_url+name


