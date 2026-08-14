from django.contrib import admin
from django.utils.html import format_html
from .models import Animal, Silhouette, Fact, AnimalSuggestion


class SilhouetteInline(admin.TabularInline):
    model = Silhouette
    extra = 0
    fields = ['image_preview', 'phylopic_uuid', 'is_primary', 'license_type', 
              'contributor_name']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 60px; width: auto;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Preview'


class FactInline(admin.TabularInline):
    model = Fact
    extra = 0
    fields = ['text_template', 'is_approved', 'is_obvious', 'difficulty', 'source']


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ['common_name', 'scientific_name', 'category', 
                    'quality_tier', 'is_published', 'is_extinct', 
                    'silhouette_preview', 'clade']
    list_filter = ['quality_tier', 'is_published', 'is_extinct', 
                   'category', 'conservation_status']
    list_editable = ['quality_tier', 'is_published']
    search_fields = ['common_name', 'scientific_name', 'slug']
    autocomplete_fields = ['clade', 'category']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SilhouetteInline, FactInline]
    ordering = ['common_name']
    
    fieldsets = (
        ('Identity', {
            'fields': ('common_name', 'scientific_name', 'slug')
        }),
        ('Tree & category', {
            'fields': ('clade', 'category')
        }),
        ('Existence', {
            'fields': ('is_extinct', 'first_appearance_mya', 
                       'last_appearance_mya', 'geologic_range',
                       'conservation_status'),
        }),
        ('Game tuning', {
            'fields': ('quality_tier', 'is_published', 'difficulty', 'popularity'),
        }),
        ('Content', {
            'fields': ('description', 'wikipedia_url'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def silhouette_preview(self, obj):
        primary = obj.silhouettes.filter(is_primary=True).first()
        if primary and primary.image:
            return format_html(
                '<img src="{}" style="height: 30px; width: auto;" />',
                primary.image.url
            )
        return '—'
    silhouette_preview.short_description = 'Silhouette'


@admin.register(Silhouette)
class SilhouetteAdmin(admin.ModelAdmin):
    list_display = ['animal', 'phylopic_uuid', 'is_primary', 'license_type', 
                    'contributor_name', 'image_preview']
    list_filter = ['is_primary', 'license_type']
    search_fields = ['animal__common_name', 'phylopic_uuid', 'contributor_name']
    autocomplete_fields = ['animal']
    readonly_fields = ['image_preview', 'created_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 80px; width: auto;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Preview'


@admin.register(Fact)
class FactAdmin(admin.ModelAdmin):
    list_display = ['animal', 'short_text', 'is_approved', 'is_obvious', 
                    'difficulty', 'times_shown', 'success_rate']
    list_filter = ['is_approved', 'is_obvious', 'difficulty']
    list_editable = ['is_approved', 'is_obvious', 'difficulty']
    search_fields = ['text_template', 'animal__common_name']
    autocomplete_fields = ['animal']
    readonly_fields = ['times_shown', 'times_correct', 'created_at', 'updated_at']

    def short_text(self, obj):
        return obj.text_template[:80] + ('…' if len(obj.text_template) > 80 else '')
    short_text.short_description = 'Fact'

    def success_rate(self, obj):
        if obj.times_shown == 0:
            return '—'
        return f"{(obj.times_correct / obj.times_shown * 100):.0f}%"
    success_rate.short_description = 'Success'


@admin.register(AnimalSuggestion)
class AnimalSuggestionAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_message', 'has_feedback', 'created_at', 'is_read']
    list_editable = ['is_read']
    list_filter = ['is_read']
    readonly_fields = ['name', 'message', 'feedback', 'created_at']

    def short_message(self, obj):
        return obj.message[:80] + ('…' if len(obj.message) > 80 else '')
    short_message.short_description = 'Message'

    def has_feedback(self, obj):
        return bool(obj.feedback)
    has_feedback.boolean = True