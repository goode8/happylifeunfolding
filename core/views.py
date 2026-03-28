from django.shortcuts import render, get_object_or_404
from .models import App, ContactMessage


def home(request):
    apps = App.objects.filter(is_published=True)
    return render(request, 'core/home.html', {'apps': apps})


def app_list(request):
    apps = App.objects.filter(is_published=True)
    return render(request, 'core/app_list.html', {'apps': apps})


def app_detail(request, slug):
    app = get_object_or_404(App, slug=slug, is_published=True)
    return render(request, 'core/app_detail.html', {
        'app': app,
        'support_url': app.get_support_url(),
        'privacy_url': app.get_privacy_url(),
    })


def app_support(request, slug):
    app = get_object_or_404(App, slug=slug, is_published=True)
    return render(request, 'core/app_support.html', {
        'app': app,
        'back_url': app.get_absolute_url(),
    })


def app_privacy(request, slug):
    app = get_object_or_404(App, slug=slug, is_published=True)
    return render(request, 'core/app_privacy.html', {
        'app': app,
        'back_url': app.get_absolute_url(),
    })


def blog(request):
    return render(request, 'core/blog.html')


def contact(request):
    submitted = False
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email, message=message
            )
            submitted = True
    return render(request, 'core/contact.html', {'submitted': submitted})
