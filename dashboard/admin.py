from django.contrib import admin
from .models import User, TableTemplate, TemplateColumn


class TemplateColumnInline(admin.TabularInline):
    model = TemplateColumn
    extra = 1
    ordering = ['order']


@admin.register(TableTemplate)
class TableTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at', 'updated_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['name', 'description']
    inlines = [TemplateColumnInline]


# Register your models here.
admin.site.register([User])
