from django.conf.urls import url
from booktest import views

urlpatterns = [
    #通过url函数设置url路由配置项
    url(r'^index$', views.index),
    url(r'^index2$', views.index2)
]