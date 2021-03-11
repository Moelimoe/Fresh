# -*- coding:gbk -*-

from django.shortcuts import HttpResponse
import time


def sayhello(request):
    print('hello ...')
    time.sleep(2)
    print('world ...')
    return HttpResponse("hello world")