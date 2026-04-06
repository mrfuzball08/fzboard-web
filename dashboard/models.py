from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class TableTemplate(models.Model):
    """
    A user-defined table template that stores column headers and their data types.
    Used to generate downloadable CSV files with the correct structure.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ['name', 'owner']

    def __str__(self):
        return self.name


class TemplateColumn(models.Model):
    """
    A single column definition within a TableTemplate.
    Stores the header name, data type, and display order.
    """
    DATA_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('integer', 'Entero'),
        ('float', 'Decimal'),
        ('date', 'Fecha'),
        ('boolean', 'Booleano'),
        ('email', 'Correo Electrónico'),
        ('url', 'URL'),
    ]

    template = models.ForeignKey(
        TableTemplate,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    name = models.CharField(max_length=255, help_text='Nombre del encabezado de columna')
    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        default='text',
        help_text='Tipo de dato de la columna'
    )
    order = models.PositiveIntegerField(default=0, help_text='Orden de la columna en la tabla')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.get_data_type_display()})"


# ──────────────────────────────────────────────
#  Dataset Ingestion Models
# ──────────────────────────────────────────────

class Dataset(models.Model):
    """
    A logical collection of uploaded tabular data tied to one template.
    One template can have multiple datasets (e.g. 'Q1 Sales', 'Q2 Sales').
    """
    STATUS_CHOICES = [
        ('empty', 'Vacío'),
        ('ready', 'Listo'),
        ('importing', 'Importando'),
        ('failed', 'Fallido'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='datasets'
    )
    template = models.ForeignKey(
        TableTemplate,
        on_delete=models.CASCADE,
        related_name='datasets'
    )
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='empty',
    )
    row_count = models.PositiveIntegerField(default=0)
    invalid_row_count = models.PositiveIntegerField(default=0)
    last_imported_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ['name', 'owner', 'template']

    def __str__(self):
        return self.name


class DatasetImport(models.Model):
    """
    Represents one upload event into a dataset.
    Tracks the original file, mapping decisions, and import results.
    """
    MODE_CHOICES = [
        ('replace', 'Reemplazar'),
        ('append', 'Agregar'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='imports'
    )
    source_filename = models.CharField(max_length=255)
    source_file = models.FileField(upload_to='imports/')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='replace')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_rows = models.PositiveIntegerField(default=0)
    inserted_rows = models.PositiveIntegerField(default=0)
    invalid_rows = models.PositiveIntegerField(default=0)
    extra_columns_json = models.JSONField(default=list, blank=True)
    missing_columns_json = models.JSONField(default=list, blank=True)
    header_mapping_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source_filename} → {self.dataset.name} ({self.get_status_display()})"


class DatasetRow(models.Model):
    """
    One imported row stored as raw structured JSON data.
    Keys in data_json are str(TemplateColumn.id) for stable references.
    """
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='rows'
    )
    dataset_import = models.ForeignKey(
        DatasetImport,
        on_delete=models.CASCADE,
        related_name='rows'
    )
    row_index = models.PositiveIntegerField()
    data_json = models.JSONField(default=dict, blank=True)
    is_valid = models.BooleanField(default=True)
    issue_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['row_index']

    def __str__(self):
        return f"Row {self.row_index} (Dataset: {self.dataset.name})"


class DatasetCellIssue(models.Model):
    """
    Validation issue found in a specific row for a specific template column.
    Rows are still stored even if they have issues.
    """
    ISSUE_CODE_CHOICES = [
        ('missing_column', 'Columna faltante'),
        ('missing_value', 'Valor faltante'),
        ('invalid_integer', 'Entero inválido'),
        ('invalid_float', 'Decimal inválido'),
        ('invalid_date', 'Fecha inválida'),
        ('invalid_boolean', 'Booleano inválido'),
        ('invalid_email', 'Email inválido'),
        ('invalid_url', 'URL inválida'),
        ('unmapped_source_column', 'Columna sin mapear'),
    ]

    dataset_row = models.ForeignKey(
        DatasetRow,
        on_delete=models.CASCADE,
        related_name='issues'
    )
    template_column = models.ForeignKey(
        TemplateColumn,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues'
    )
    raw_value = models.TextField(null=True, blank=True)
    issue_code = models.CharField(max_length=30, choices=ISSUE_CODE_CHOICES)
    message = models.CharField(max_length=255)

    def __str__(self):
        col_name = self.template_column.name if self.template_column else 'N/A'
        return f"Issue: {col_name} — {self.get_issue_code_display()}"


# ──────────────────────────────────────────────
#  Reporting Models
# ──────────────────────────────────────────────

class Report(models.Model):
    """
    A saved report definition tied to a specific dataset.
    Contains widgets (charts/tables) and global filters.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    layout_json = models.JSONField(default=dict, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ['name', 'owner', 'dataset']

    def __str__(self):
        return self.name


class ReportWidget(models.Model):
    """
    One chart or table inside a report.
    Stores dimensions, metrics, filters, and widget-specific settings in config_json.
    """
    WIDGET_TYPE_CHOICES = [
        ('table', 'Tabla'),
        ('bar', 'Barras'),
        ('pie', 'Pastel'),
        ('scatter', 'Dispersión'),
        ('histogram', 'Histograma'),
    ]

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES, default='table')
    config_json = models.JSONField(default=dict, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    # Layout positions — reserved for future grid/canvas layout
    layout_x = models.PositiveIntegerField(default=0)
    layout_y = models.PositiveIntegerField(default=0)
    layout_w = models.PositiveIntegerField(default=12)
    layout_h = models.PositiveIntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"


class ReportFilter(models.Model):
    """
    Report-level global filter that applies to all widgets by default.
    Widgets can override filters via their own config_json.filters.
    """
    FIELD_KIND_CHOICES = [
        ('template_column', 'Columna del Formato'),
        ('calculated_field', 'Campo Calculado'),
    ]
    OPERATOR_CHOICES = [
        ('equals', 'Igual a'),
        ('not_equals', 'Diferente de'),
        ('contains', 'Contiene'),
        ('not_contains', 'No contiene'),
        ('in_list', 'En lista'),
        ('gt', 'Mayor que'),
        ('gte', 'Mayor o igual que'),
        ('lt', 'Menor que'),
        ('lte', 'Menor o igual que'),
        ('between', 'Entre'),
        ('is_null', 'Es vacío'),
        ('is_not_null', 'No es vacío'),
    ]

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='filters'
    )
    field_kind = models.CharField(max_length=20, choices=FIELD_KIND_CHOICES, default='template_column')
    field_ref = models.PositiveIntegerField(help_text='ID de la columna o campo calculado')
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES, default='equals')
    value_json = models.JSONField(
        default=dict, blank=True,
        help_text='{"value": ...} para escalar, {"values": [...]} para lista, {"min": ..., "max": ...} para rango'
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Filter: {self.get_field_kind_display()} #{self.field_ref} {self.get_operator_display()}"
