from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('apps/', views.app_list, name='app_list'),

    # ── Tia T-Rex deep link routes ───────────────────────────────
    # Must come BEFORE the generic apps/<slug>/ pattern.
    path('apps/tiatrex/daily/', views.tiatrex_daily, name='tia_daily'),
    path('apps/tiatrex/daily/<str:date>/', views.tiatrex_daily_date, name='tiatrex_daily_date'),
    # ──────────────────────────────────────────────────────────────────────

    path('apps/<slug:slug>/', views.app_detail, name='app_detail'),
    path('apps/<slug:slug>/support/', views.app_support, name='app_support'),
    path('apps/<slug:slug>/privacy/', views.app_privacy, name='app_privacy'),
    path('about/', views.about, name='about'),
    # path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
]
