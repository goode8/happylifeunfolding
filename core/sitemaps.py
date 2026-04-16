from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import App


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return ['home', 'app_list', 'about', 'contact']

    def location(self, item):
        return reverse(item)


class AppSitemap(Sitemap):
    priority = 0.6
    changefreq = 'monthly'

    def items(self):
        return App.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at
