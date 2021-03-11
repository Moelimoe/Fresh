# -*- coding:gbk -*-
from django.conf.urls import url
from booktest import views

urlpatterns = [
    url(r'^hi$', views.sayhello, name='hello'),
]