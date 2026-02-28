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
