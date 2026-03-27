from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='beingneighborly-index'),
    path('support/', views.support, name='beingneighborly-support'),
    path('privacy/', views.privacy, name='beingneighborly-privacy'),
]
