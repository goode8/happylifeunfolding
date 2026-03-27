from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='myunclethetrex-index'),
    path('support/', views.support, name='myunclethetrex-support'),
    path('privacy/', views.privacy, name='myunclethetrex-privacy'),
]
