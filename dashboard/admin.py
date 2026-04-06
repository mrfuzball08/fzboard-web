from django.contrib import admin
from .models import (
    User, TableTemplate, TemplateColumn,
    Dataset, DatasetImport, DatasetRow, DatasetCellIssue,
    Report, ReportWidget, ReportFilter,
)


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


class DatasetImportInline(admin.TabularInline):
    model = DatasetImport
    extra = 0
    readonly_fields = ['source_filename', 'mode', 'status', 'total_rows', 'inserted_rows', 'invalid_rows', 'created_at']
    show_change_link = True


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'template', 'status', 'row_count', 'invalid_row_count', 'created_at']
    list_filter = ['status', 'owner', 'created_at']
    search_fields = ['name']
    inlines = [DatasetImportInline]


@admin.register(DatasetImport)
class DatasetImportAdmin(admin.ModelAdmin):
    list_display = ['source_filename', 'dataset', 'mode', 'status', 'total_rows', 'inserted_rows', 'invalid_rows', 'created_at']
    list_filter = ['status', 'mode', 'created_at']
    search_fields = ['source_filename']
    readonly_fields = ['extra_columns_json', 'missing_columns_json', 'header_mapping_json']


@admin.register(DatasetRow)
class DatasetRowAdmin(admin.ModelAdmin):
    list_display = ['row_index', 'dataset', 'is_valid', 'issue_count', 'created_at']
    list_filter = ['is_valid', 'dataset']
    readonly_fields = ['data_json']
    list_per_page = 50


@admin.register(DatasetCellIssue)
class DatasetCellIssueAdmin(admin.ModelAdmin):
    list_display = ['dataset_row', 'template_column', 'issue_code', 'raw_value', 'message']
    list_filter = ['issue_code']
    search_fields = ['message', 'raw_value']


# ──────────────────────────────────────────────
#  Report Admin
# ──────────────────────────────────────────────

class ReportWidgetInline(admin.TabularInline):
    model = ReportWidget
    extra = 0
    ordering = ['sort_order']
    readonly_fields = ['config_json']
    show_change_link = True


class ReportFilterInline(admin.TabularInline):
    model = ReportFilter
    extra = 0
    ordering = ['sort_order']
    readonly_fields = ['value_json']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'dataset', 'widget_count', 'created_at', 'updated_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ReportWidgetInline, ReportFilterInline]

    def widget_count(self, obj):
        return obj.widgets.count()
    widget_count.short_description = 'Widgets'


@admin.register(ReportWidget)
class ReportWidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'report', 'widget_type', 'sort_order', 'created_at']
    list_filter = ['widget_type']
    search_fields = ['title']
    readonly_fields = ['config_json']


@admin.register(ReportFilter)
class ReportFilterAdmin(admin.ModelAdmin):
    list_display = ['report', 'field_kind', 'field_ref', 'operator', 'sort_order']
    list_filter = ['field_kind', 'operator']
    readonly_fields = ['value_json']


# Register your models here.
admin.site.register([User])

