from django.contrib import admin
from .models import App, ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at', 'is_read']
    list_editable = ['is_read']
    readonly_fields = ['name', 'email', 'message', 'created_at']


@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_published', 'order', 'updated_at']
    list_editable = ['is_published', 'order']
    list_filter = ['category', 'is_published']
    search_fields = ['name', 'tagline']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Core', {
            'fields': ('name', 'slug', 'emoji', 'category', 'tagline', 'description', 'accent_color')
        }),
        ('Store Links', {
            'fields': ('product_url', 'product_url_label', 'app_store_url', 'play_store_url', 'support_email')
        }),
        ('Apple / Google Required', {
            'fields': ('support_url_notes', 'privacy_policy'),
            'description': 'These power the /support/ and /privacy/ pages Apple and Google require.'
        }),
        ('Display', {
            'fields': ('is_published', 'order')
        }),
    )
