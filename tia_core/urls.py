from django.urls import re_path, path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='play/'), name='home'),
    path('play/', views.play_hub, name='play'),
    path('play/daily/', views.game, name='daily_game'),
    path('play/match/', views.match_up, name='match_up'),
    path('play/creature/', views.creature_of_day, name='creature_of_day'),
    path('explore/', views.explore, name='explore'),
    path('credits/', views.credits, name='credits'),
    re_path(
        r'^phylo-img/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.png$',
        views.phylo_image,
        name='phylo_image',
    ),
]
