from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('test/', views.test, name='test'),
    path('stop/<int:pid>/', views.stop, name='stop'),
    path('<str:display_name_short>/play/', views.play, name='play'),
]
