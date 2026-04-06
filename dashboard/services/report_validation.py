"""
Widget configuration validation.

Validates that a widget's config_json is compatible with its type
and that all field references, aggregations, and operators are valid
for the referenced data types.
"""

from .report_fields import (
    resolve_field, get_allowed_aggregations, get_allowed_group_bys,
    get_allowed_operators, is_numeric_type,
)


def validate_widget_config(widget_type, config_json, dataset):
    """
    Validate a widget configuration against its type and the dataset's schema.

    Returns (is_valid: bool, errors: list[str]).
    """
    errors = []
    config = config_json or {}
    dimensions = config.get('dimensions', [])
    metrics = config.get('metrics', [])
    filters = config.get('filters', [])

    # ─── Type-specific structural rules ───────────────────────────
    if widget_type == 'table':
        # Table can have dimensions only (no metrics required)
        if not dimensions and not metrics:
            errors.append("Una tabla necesita al menos una dimensión o una métrica.")

    elif widget_type == 'bar':
        if not dimensions:
            errors.append("Un gráfico de barras necesita al menos una dimensión.")
        if not metrics:
            errors.append("Un gráfico de barras necesita al menos una métrica.")

    elif widget_type == 'pie':
        if len(dimensions) != 1:
            errors.append("Un gráfico de pastel necesita exactamente una dimensión.")
        if len(metrics) != 1:
            errors.append("Un gráfico de pastel necesita exactamente una métrica.")

    elif widget_type == 'scatter':
        if len(metrics) < 2:
            errors.append("Un gráfico de dispersión necesita al menos dos métricas numéricas (X e Y).")
        # Validate that the first two metrics are numeric
        for i, m in enumerate(metrics[:2]):
            try:
                info = resolve_field(
                    m.get('field_kind', 'template_column'),
                    m.get('field_ref'), dataset
                )
                if not is_numeric_type(info['data_type']):
                    axis = 'X' if i == 0 else 'Y'
                    errors.append(f"El eje {axis} del gráfico de dispersión debe ser un campo numérico, no '{info['data_type']}'.")
            except ValueError as e:
                errors.append(str(e))

    elif widget_type == 'histogram':
        if len(metrics) != 1:
            errors.append("Un histograma necesita exactamente una métrica.")
        if metrics:
            try:
                info = resolve_field(
                    metrics[0].get('field_kind', 'template_column'),
                    metrics[0].get('field_ref'), dataset
                )
                if not is_numeric_type(info['data_type']):
                    errors.append(f"El histograma requiere un campo numérico, no '{info['data_type']}'.")
            except ValueError as e:
                errors.append(str(e))

    else:
        errors.append(f"Tipo de widget desconocido: '{widget_type}'.")

    # ─── Validate all dimension fields ────────────────────────────
    for i, dim in enumerate(dimensions):
        field_kind = dim.get('field_kind', 'template_column')
        field_ref = dim.get('field_ref')
        group_by = dim.get('group_by', 'raw')

        try:
            info = resolve_field(field_kind, field_ref, dataset)
        except ValueError as e:
            errors.append(f"Dimensión {i+1}: {e}")
            continue

        allowed_gbs = get_allowed_group_bys(info['data_type'])
        if group_by not in allowed_gbs:
            errors.append(
                f"Dimensión '{info['name']}': agrupación '{group_by}' no válida "
                f"para tipo '{info['data_type']}'. Opciones: {', '.join(allowed_gbs)}."
            )

    # ─── Validate all metric fields ───────────────────────────────
    for i, met in enumerate(metrics):
        field_kind = met.get('field_kind', 'template_column')
        field_ref = met.get('field_ref')
        aggregation = met.get('aggregation', 'count')

        try:
            info = resolve_field(field_kind, field_ref, dataset)
        except ValueError as e:
            errors.append(f"Métrica {i+1}: {e}")
            continue

        allowed_aggs = get_allowed_aggregations(info['data_type'])
        if aggregation not in allowed_aggs:
            errors.append(
                f"Métrica '{info['name']}': agregación '{aggregation}' no válida "
                f"para tipo '{info['data_type']}'. Opciones: {', '.join(allowed_aggs)}."
            )

    # ─── Validate widget-level filters ────────────────────────────
    for i, flt in enumerate(filters):
        field_kind = flt.get('field_kind', 'template_column')
        field_ref = flt.get('field_ref')
        operator = flt.get('operator', 'equals')

        try:
            info = resolve_field(field_kind, field_ref, dataset)
        except ValueError as e:
            errors.append(f"Filtro {i+1}: {e}")
            continue

        allowed_ops = get_allowed_operators(info['data_type'])
        if operator not in allowed_ops:
            errors.append(
                f"Filtro '{info['name']}': operador '{operator}' no válido "
                f"para tipo '{info['data_type']}'. Opciones: {', '.join(allowed_ops)}."
            )

    return (len(errors) == 0, errors)
