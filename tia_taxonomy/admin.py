from django.contrib import admin
from .models import Clade, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['parent_group', 'sub_group', 'display_order', 'animal_count']
    list_editable = ['display_order']
    search_fields = ['parent_group', 'sub_group']
    ordering = ['display_order', 'parent_group', 'sub_group']

    def animal_count(self, obj):
        return obj.animals.count()
    animal_count.short_description = 'Animals'


@admin.register(Clade)
class CladeAdmin(admin.ModelAdmin):
    list_display = ['name', 'rank', 'depth', 'parent', 'divergence_mya', 
                    'divergence_source', 'animal_count']
    list_filter = ['rank', 'divergence_source', 'divergence_confidence', 'depth']
    search_fields = ['name', 'slug']
    readonly_fields = ['path', 'depth', 'created_at', 'updated_at']
    autocomplete_fields = ['parent']
    ordering = ['depth', 'name']
    
    fieldsets = (
        ('Identity', {
            'fields': ('name', 'slug', 'rank', 'ott_id')
        }),
        ('Tree position', {
            'fields': ('parent', 'path', 'depth'),
        }),
        ('Divergence date', {
            'fields': ('divergence_mya', 'divergence_source', 'divergence_confidence'),
        }),
        ('Story', {
            'fields': ('description', 'notable_traits'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def animal_count(self, obj):
        return obj.animals.count()
    animal_count.short_description = 'Animals'