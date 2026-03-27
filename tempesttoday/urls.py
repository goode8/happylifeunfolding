from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='tempesttoday-index'),
    path('support/', views.support, name='tempesttoday-support'),
    path('privacy/', views.privacy, name='tempesttoday-privacy'),
]
