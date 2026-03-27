from django.shortcuts import render, get_object_or_404
from core.models import App

SLUG = 'my-uncle-the-t-rex'


def index(request):
    app = get_object_or_404(App, slug=SLUG, is_published=True)
    return render(request, 'core/app_detail.html', {
        'app': app,
        'support_url': '/support/',
        'privacy_url': '/privacy/',
    })


def support(request):
    app = get_object_or_404(App, slug=SLUG, is_published=True)
    return render(request, 'core/app_support.html', {
        'app': app,
        'back_url': '/',
    })


def privacy(request):
    app = get_object_or_404(App, slug=SLUG, is_published=True)
    return render(request, 'core/app_privacy.html', {
        'app': app,
        'back_url': '/',
    })
