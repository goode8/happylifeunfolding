from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('apps/', views.app_list, name='app_list'),
    path('apps/<slug:slug>/', views.app_detail, name='app_detail'),
    path('apps/<slug:slug>/support/', views.app_support, name='app_support'),
    path('apps/<slug:slug>/privacy/', views.app_privacy, name='app_privacy'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
]
