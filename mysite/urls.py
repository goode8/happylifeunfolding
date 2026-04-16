import os
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from core.views import apple_app_site_association

SECRET_ADMIN_URL_PATH = os.environ.get('SECRET_ADMIN_URL_PATH', 'default-fallback')


def robots_txt(request):
    lines = [
        "# Allow major search engines",
        "User-agent: Googlebot",
        "User-agent: Bingbot",
        "User-agent: Slurp",
        "User-agent: DuckDuckBot",
        "Allow: /",
        "",
        "# Allow social media crawlers",
        "User-agent: facebookexternalhit",
        "User-agent: Twitterbot",
        "User-agent: LinkedInBot",
        "Allow: /",
        "",
        "# Allow OpenAI SearchBot",
        "User-agent: OAI-SearchBot",
        "Allow: /",
        "",
        "# Block SEO crawlers",
        "User-agent: SemrushBot",
        "User-agent: AhrefsBot",
        "User-agent: MJ12bot",
        "User-agent: DotBot",
        "Disallow: /",
        "",
        "# Block everything else",
        "User-agent: *",
        "Disallow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


urlpatterns = [
    path('robots.txt', robots_txt),

    # Apple Universal Links — must be served at domain root, no redirects
    path('.well-known/apple-app-site-association', apple_app_site_association, name='aasa'),

    path("", include("core.urls")),
    path(f"{SECRET_ADMIN_URL_PATH}/", admin.site.urls),
]
