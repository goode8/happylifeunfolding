import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from .models import App, ContactMessage

# ── My Uncle the T-Rex smart app linking ─────────────────────────────────────

MUTT_APP_STORE_URL = "https://apps.apple.com/app/idYOUR_APP_ID"          # fill in when published
MUTT_PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.yourname.myunclethetrex"
MUTT_BUNDLE_ID = "com.yourname.myunclethetrex"
MUTT_TEAM_ID = "XXXXXXXXXX"   # fill in when you have your Apple Team ID


def _detect_device(request):
    """Return 'ios', 'android', or 'desktop' based on User-Agent."""
    ua = request.META.get("HTTP_USER_AGENT", "").lower()
    if "iphone" in ua or "ipad" in ua or "ipod" in ua:
        return "ios"
    if "android" in ua:
        return "android"
    return "desktop"


def myunclethetrex_daily(request):
    """/daily — redirect mobile to store, desktop to app detail page."""
    device = _detect_device(request)
    if device == "ios":
        return redirect(MUTT_APP_STORE_URL)
    if device == "android":
        return redirect(MUTT_PLAY_STORE_URL)
    return redirect("app_detail", slug="my-uncle-the-t-rex")


def myunclethetrex_daily_date(request, date):
    """/daily/<date> — redirect mobile to store, desktop to app detail page."""
    device = _detect_device(request)
    if device == "ios":
        return redirect(MUTT_APP_STORE_URL)
    if device == "android":
        return redirect(f"{MUTT_PLAY_STORE_URL}&deep_link=daily/{date}")
    return redirect("app_detail", slug="my-uncle-the-t-rex")


def apple_app_site_association(request):
    """
    /.well-known/apple-app-site-association
    Required for Universal Links (iOS). Apple fetches this on app install
    from the domain listed in the app's Associated Domains entitlement.
    Use applinks:happylifeunfolding.com in your app entitlements.
    """
    aasa = {
        "applinks": {
            "apps": [],
            "details": [
                {
                    # Format: TEAMID.BUNDLEID
                    "appID": f"{MUTT_TEAM_ID}.{MUTT_BUNDLE_ID}",
                    "paths": [
                        "/apps/my-uncle-the-t-rex",
                        "/apps/my-uncle-the-t-rex/*",
                    ],
                }
            ],
        }
    }
    return HttpResponse(
        json.dumps(aasa),
        content_type="application/json",
    )


def home(request):
    apps = App.objects.filter(is_published=True)
    return render(request, 'core/home.html', {'apps': apps})


def app_list(request):
    apps = App.objects.filter(is_published=True)
    return render(request, 'core/app_list.html', {'apps': apps})


def app_detail(request, slug):
    app = get_object_or_404(App, slug=slug, is_published=True)
    device = _detect_device(request)
    if device == "ios" and app.app_store_url:
        return redirect(app.app_store_url)
    if device == "android" and app.play_store_url:
        return redirect(app.play_store_url)
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
