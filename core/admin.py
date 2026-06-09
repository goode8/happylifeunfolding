from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from .models import App, ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at', 'is_read']
    list_editable = ['is_read']
    readonly_fields = ['name', 'email', 'message', 'created_at']
    change_form_template = 'admin/core/contactmessage/change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/delete-now/', self.admin_site.admin_view(self.delete_now_view), name='core_contactmessage_delete_now'),
        ]
        return custom + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            next_obj = ContactMessage.objects.filter(created_at__lt=obj.created_at).order_by('-created_at').first()
            prev_obj = ContactMessage.objects.filter(created_at__gt=obj.created_at).order_by('created_at').first()
            extra_context['next_id'] = next_obj.pk if next_obj else None
            extra_context['prev_id'] = prev_obj.pk if prev_obj else None
        return super().change_view(request, object_id, form_url, extra_context)

    def delete_now_view(self, request, pk):
        obj = get_object_or_404(ContactMessage, pk=pk)
        next_obj = ContactMessage.objects.filter(created_at__lt=obj.created_at).order_by('-created_at').first()
        obj.delete()
        if next_obj:
            return redirect(reverse('admin:core_contactmessage_change', args=[next_obj.pk]))
        return redirect(reverse('admin:core_contactmessage_changelist'))


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
