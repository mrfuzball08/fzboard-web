"""
Field resolution and type-aware operation rules.

Maps each TemplateColumn.data_type to its allowed aggregations,
group-by modes, and filter operators. Used by report_validation
and report_query to enforce valid configurations.
"""

from dashboard.models import TemplateColumn

# ──────────────────────────────────────────────
#  Type-aware Rules
# ──────────────────────────────────────────────

FIELD_RULES = {
    'text': {
        'aggregations': ['count', 'distinct_count'],
        'group_bys': ['raw'],
        'operators': ['equals', 'not_equals', 'contains', 'not_contains', 'in_list', 'is_null', 'is_not_null'],
    },
    'integer': {
        'aggregations': ['sum', 'avg', 'min', 'max', 'count'],
        'group_bys': ['raw'],
        'operators': ['equals', 'not_equals', 'gt', 'gte', 'lt', 'lte', 'between', 'is_null', 'is_not_null'],
    },
    'float': {
        'aggregations': ['sum', 'avg', 'min', 'max', 'count'],
        'group_bys': ['raw'],
        'operators': ['equals', 'not_equals', 'gt', 'gte', 'lt', 'lte', 'between', 'is_null', 'is_not_null'],
    },
    'date': {
        'aggregations': ['count', 'min', 'max'],
        'group_bys': ['raw', 'day', 'week', 'month', 'year'],
        'operators': ['equals', 'not_equals', 'gt', 'gte', 'lt', 'lte', 'between', 'is_null', 'is_not_null'],
    },
    'boolean': {
        'aggregations': ['count'],
        'group_bys': ['raw'],
        'operators': ['equals', 'is_null', 'is_not_null'],
    },
    'email': {
        'aggregations': ['count', 'distinct_count'],
        'group_bys': ['raw'],
        'operators': ['equals', 'not_equals', 'contains', 'not_contains', 'in_list', 'is_null', 'is_not_null'],
    },
    'url': {
        'aggregations': ['count', 'distinct_count'],
        'group_bys': ['raw'],
        'operators': ['equals', 'not_equals', 'contains', 'not_contains', 'in_list', 'is_null', 'is_not_null'],
    },
}

NUMERIC_TYPES = {'integer', 'float'}


def resolve_field(field_kind, field_ref, dataset):
    """
    Resolve a field reference to its info.

    Returns dict: { 'id': int, 'name': str, 'data_type': str, 'column': TemplateColumn }
    Raises ValueError if the field cannot be resolved.
    """
    if field_kind == 'template_column':
        try:
            col = dataset.template.columns.get(pk=field_ref)
            return {
                'id': col.id,
                'name': col.name,
                'data_type': col.data_type,
                'column': col,
            }
        except TemplateColumn.DoesNotExist:
            raise ValueError(f"Columna #{field_ref} no encontrada en el formato '{dataset.template.name}'")
    elif field_kind == 'calculated_field':
        # Phase 4 — calculated fields not yet implemented
        raise ValueError("Los campos calculados aún no están implementados")
    else:
        raise ValueError(f"Tipo de campo desconocido: '{field_kind}'")


def get_allowed_aggregations(data_type):
    """Return list of valid aggregation functions for the given data type."""
    rules = FIELD_RULES.get(data_type, {})
    return rules.get('aggregations', [])


def get_allowed_group_bys(data_type):
    """Return list of valid group-by modes for the given data type."""
    rules = FIELD_RULES.get(data_type, {})
    return rules.get('group_bys', [])


def get_allowed_operators(data_type):
    """Return list of valid filter operators for the given data type."""
    rules = FIELD_RULES.get(data_type, {})
    return rules.get('operators', [])


def is_numeric_type(data_type):
    """Check if a data type supports numeric operations (sum, avg, etc.)."""
    return data_type in NUMERIC_TYPES


def get_all_field_info(dataset):
    """
    Return all available fields for a dataset as a list of dicts.
    Used by the builder UI to populate dropdowns.
    """
    columns = dataset.template.columns.all()
    fields = []
    for col in columns:
        rules = FIELD_RULES.get(col.data_type, {})
        fields.append({
            'id': col.id,
            'name': col.name,
            'data_type': col.data_type,
            'data_type_display': col.get_data_type_display(),
            'field_kind': 'template_column',
            'aggregations': rules.get('aggregations', []),
            'group_bys': rules.get('group_bys', []),
            'operators': rules.get('operators', []),
            'is_numeric': col.data_type in NUMERIC_TYPES,
        })
    return fields
