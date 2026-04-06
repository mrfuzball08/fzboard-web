"""
Pandas-based query execution engine for report widgets.

Loads dataset rows into a DataFrame, casts types, applies filters,
groups/aggregates, sorts, and formats results for both table rendering
and Chart.js-compatible output.
"""

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

from dashboard.models import DatasetRow, TemplateColumn
from .report_fields import resolve_field, is_numeric_type, FIELD_RULES


@dataclass
class QueryResult:
    """Result of executing a widget query."""
    columns: list = field(default_factory=list)    # [{"key": str, "label": str, "type": str}]
    rows: list = field(default_factory=list)       # [{key: value, ...}, ...]
    total_rows: int = 0
    excluded_invalid: int = 0
    warnings: list = field(default_factory=list)
    chart_data: dict = field(default_factory=dict)  # formatted for Chart.js


def execute_widget(widget, report):
    """
    Execute the query engine for a single widget.

    Args:
        widget: ReportWidget instance (or a dict with widget_type + config_json)
        report: Report instance

    Returns:
        QueryResult
    """
    dataset = report.dataset

    # Support both model instances and dicts (for preview)
    if isinstance(widget, dict):
        widget_type = widget.get('widget_type', 'table')
        config = widget.get('config_json', {})
    else:
        widget_type = widget.widget_type
        config = widget.config_json or {}

    dimensions = config.get('dimensions', [])
    metrics = config.get('metrics', [])
    widget_filters = config.get('filters', [])
    sort_spec = config.get('sort', [])
    options = config.get('options', {})
    limit = options.get('limit', 500)

    result = QueryResult()

    # ─── 1. Load data ─────────────────────────────────────────────
    rows_qs = DatasetRow.objects.filter(dataset=dataset).values_list('data_json', flat=True)
    raw_data = list(rows_qs)

    if not raw_data:
        result.warnings.append("El dataset no tiene datos.")
        return result

    # Build a DataFrame from data_json dicts
    df = pd.DataFrame(raw_data)

    # ─── 2. Resolve fields and cast types ─────────────────────────
    columns_by_id = {}
    all_col_ids = set()

    for dim in dimensions:
        ref = dim.get('field_ref')
        if ref:
            all_col_ids.add(str(ref))
    for met in metrics:
        ref = met.get('field_ref')
        if ref:
            all_col_ids.add(str(ref))
    for flt in widget_filters:
        ref = flt.get('field_ref')
        if ref:
            all_col_ids.add(str(ref))

    # Also include report-level filter fields
    for rf in report.filters.all():
        all_col_ids.add(str(rf.field_ref))

    for col_id_str in all_col_ids:
        try:
            col = dataset.template.columns.get(pk=int(col_id_str))
            columns_by_id[col_id_str] = col
        except (TemplateColumn.DoesNotExist, ValueError):
            result.warnings.append(f"Columna #{col_id_str} no encontrada, ignorando.")

    # Ensure all referenced columns exist in the DF
    for col_id_str in all_col_ids:
        if col_id_str not in df.columns:
            df[col_id_str] = None

    # Cast types
    original_len = len(df)
    for col_id_str, col in columns_by_id.items():
        if col_id_str not in df.columns:
            continue
        df[col_id_str] = _cast_column(df[col_id_str], col.data_type)

    # ─── 3. Apply report-level filters ────────────────────────────
    for rf in report.filters.all():
        df = _apply_filter(df, str(rf.field_ref), rf.operator, rf.value_json, columns_by_id, result)

    # ─── 4. Apply widget-level filters ────────────────────────────
    for flt in widget_filters:
        ref = str(flt.get('field_ref', ''))
        operator = flt.get('operator', 'equals')
        value = flt.get('value', {})
        if isinstance(value, dict):
            value_json = value
        else:
            value_json = {'value': value}
        df = _apply_filter(df, ref, operator, value_json, columns_by_id, result)

    # Track excluded rows
    result.excluded_invalid = original_len - len(df)

    # ─── 5. Build result based on widget type ─────────────────────
    if widget_type == 'histogram':
        result = _execute_histogram(df, metrics, columns_by_id, options, result)
    elif widget_type == 'scatter':
        result = _execute_scatter(df, metrics, dimensions, columns_by_id, options, result)
    elif dimensions or metrics:
        result = _execute_grouped(df, widget_type, dimensions, metrics, columns_by_id, sort_spec, limit, result)
    else:
        result.warnings.append("No se configuraron dimensiones ni métricas.")

    result.total_rows = len(result.rows)
    return result


# ──────────────────────────────────────────────
#  Internal Helpers
# ──────────────────────────────────────────────

def _cast_column(series, data_type):
    """Cast a pandas Series to the appropriate type based on data_type."""
    if data_type in ('integer',):
        return pd.to_numeric(series, errors='coerce').astype('Int64')
    elif data_type in ('float',):
        return pd.to_numeric(series, errors='coerce')
    elif data_type in ('date',):
        return pd.to_datetime(series, errors='coerce', format='mixed')
    elif data_type in ('boolean',):
        true_vals = {'true', 'yes', 'si', 'sí', '1', 'verdadero', 'v'}
        false_vals = {'false', 'no', '0', 'falso', 'f'}
        def _to_bool(val):
            if pd.isna(val) or val is None:
                return None
            s = str(val).strip().lower()
            if s in true_vals:
                return True
            if s in false_vals:
                return False
            return None
        return series.apply(_to_bool)
    else:
        # text, email, url — keep as string
        return series.astype(str).replace({'nan': None, 'None': None, '': None})


def _apply_filter(df, field_ref, operator, value_json, columns_by_id, result):
    """Apply a single filter to the DataFrame."""
    if field_ref not in df.columns:
        return df

    col = df[field_ref]
    v = value_json if isinstance(value_json, dict) else {'value': value_json}

    try:
        if operator == 'equals':
            val = v.get('value')
            mask = col == val
        elif operator == 'not_equals':
            val = v.get('value')
            mask = col != val
        elif operator == 'contains':
            val = str(v.get('value', ''))
            mask = col.astype(str).str.contains(val, case=False, na=False)
        elif operator == 'not_contains':
            val = str(v.get('value', ''))
            mask = ~col.astype(str).str.contains(val, case=False, na=False)
        elif operator == 'in_list':
            vals = v.get('values', [])
            mask = col.isin(vals)
        elif operator == 'gt':
            val = v.get('value')
            mask = col > val
        elif operator == 'gte':
            val = v.get('value')
            mask = col >= val
        elif operator == 'lt':
            val = v.get('value')
            mask = col < val
        elif operator == 'lte':
            val = v.get('value')
            mask = col <= val
        elif operator == 'between':
            lo = v.get('min')
            hi = v.get('max')
            mask = (col >= lo) & (col <= hi)
        elif operator == 'is_null':
            mask = col.isna()
        elif operator == 'is_not_null':
            mask = col.notna()
        else:
            result.warnings.append(f"Operador desconocido: '{operator}'")
            return df

        return df[mask].copy()

    except Exception as e:
        result.warnings.append(f"Error aplicando filtro: {e}")
        return df


def _execute_grouped(df, widget_type, dimensions, metrics, columns_by_id, sort_spec, limit, result):
    """Execute a grouped aggregation query (table, bar, pie)."""

    # Build group-by columns
    group_cols = []
    group_labels = []

    for dim in dimensions:
        ref = str(dim.get('field_ref', ''))
        group_by = dim.get('group_by', 'raw')
        col_info = columns_by_id.get(ref)
        col_name = col_info.name if col_info else f"Col #{ref}"

        if group_by == 'raw':
            group_cols.append(ref)
            group_labels.append(col_name)
        elif group_by in ('day', 'week', 'month', 'year') and ref in df.columns:
            # Temporal grouping
            new_col = f"_group_{ref}_{group_by}"
            if group_by == 'day':
                df[new_col] = df[ref].dt.date.astype(str)
            elif group_by == 'week':
                df[new_col] = df[ref].dt.isocalendar().week.astype(str)
            elif group_by == 'month':
                df[new_col] = df[ref].dt.to_period('M').astype(str)
            elif group_by == 'year':
                df[new_col] = df[ref].dt.year.astype(str)
            group_cols.append(new_col)
            group_labels.append(f"{col_name} ({group_by})")

    # If no dimensions, aggregate the whole dataset
    if not group_cols:
        agg_row = {}
        for i, met in enumerate(metrics):
            ref = str(met.get('field_ref', ''))
            agg = met.get('aggregation', 'count')
            label = met.get('label', f"Métrica {i+1}")
            key = f"metric_{i}"
            agg_row[key] = _aggregate_single(df, ref, agg)
            result.columns.append({'key': key, 'label': label, 'type': 'metric'})
        result.rows = [agg_row]
        return result

    # Drop NaN in group columns for clean grouping
    df_clean = df.dropna(subset=[c for c in group_cols if c in df.columns])

    if df_clean.empty:
        result.warnings.append("No hay datos después de aplicar filtros.")
        return result

    grouped = df_clean.groupby(group_cols, dropna=False)

    # Build aggregations
    agg_dict = {}
    metric_keys = []
    for i, met in enumerate(metrics):
        ref = str(met.get('field_ref', ''))
        agg = met.get('aggregation', 'count')
        label = met.get('label', f"Métrica {i+1}")
        key = f"metric_{i}"
        metric_keys.append(key)
        result.columns.append({'key': key, 'label': label, 'type': 'metric'})

    # Add dimension columns to result
    for i, label in enumerate(group_labels):
        key = f"dim_{i}"
        result.columns.insert(i, {'key': key, 'label': label, 'type': 'dimension'})

    # Aggregate
    agg_results = []
    for group_key, group_df in grouped:
        row = {}
        # Handle single vs multi group keys
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        for i, gval in enumerate(group_key):
            row[f"dim_{i}"] = _serialize_value(gval)

        for i, met in enumerate(metrics):
            ref = str(met.get('field_ref', ''))
            agg = met.get('aggregation', 'count')
            row[f"metric_{i}"] = _aggregate_single(group_df, ref, agg)

        agg_results.append(row)

    # Sort
    if sort_spec:
        for sort_item in reversed(sort_spec):
            target = sort_item.get('target', '')
            direction = sort_item.get('direction', 'asc')
            reverse = direction == 'desc'
            if ':' in target:
                prefix, idx_str = target.split(':', 1)
                key = f"{prefix}_{idx_str}"
                try:
                    agg_results.sort(key=lambda r: (r.get(key) is None, r.get(key, 0)), reverse=reverse)
                except TypeError:
                    pass

    # Limit
    if limit and len(agg_results) > limit:
        agg_results = agg_results[:limit]
        result.warnings.append(f"Resultados limitados a {limit} filas.")

    result.rows = agg_results

    # Build chart data
    if widget_type in ('bar', 'pie'):
        result.chart_data = _build_bar_pie_chart(widget_type, result)

    return result


def _execute_histogram(df, metrics, columns_by_id, options, result):
    """Execute a histogram aggregation — bins a numeric column."""
    if not metrics:
        return result

    ref = str(metrics[0].get('field_ref', ''))
    col_info = columns_by_id.get(ref)
    col_name = col_info.name if col_info else f"Col #{ref}"
    num_bins = options.get('bins', 10)

    if ref not in df.columns:
        result.warnings.append(f"Columna '{col_name}' no encontrada.")
        return result

    series = pd.to_numeric(df[ref], errors='coerce').dropna()

    if series.empty:
        result.warnings.append(f"No hay datos numéricos válidos en '{col_name}'.")
        return result

    counts, bin_edges = np.histogram(series, bins=num_bins)

    labels = []
    for i in range(len(counts)):
        lo = round(bin_edges[i], 2)
        hi = round(bin_edges[i + 1], 2)
        labels.append(f"{lo} – {hi}")

    result.columns = [
        {'key': 'bin', 'label': col_name, 'type': 'dimension'},
        {'key': 'count', 'label': 'Cantidad', 'type': 'metric'},
    ]
    result.rows = [
        {'bin': labels[i], 'count': int(counts[i])}
        for i in range(len(counts))
    ]

    result.chart_data = {
        'type': 'bar',
        'data': {
            'labels': labels,
            'datasets': [{
                'label': f'Distribución de {col_name}',
                'data': [int(c) for c in counts],
            }],
        },
    }

    return result


def _execute_scatter(df, metrics, dimensions, columns_by_id, options, result):
    """Execute a scatter plot — two numeric axes."""
    if len(metrics) < 2:
        return result

    x_ref = str(metrics[0].get('field_ref', ''))
    y_ref = str(metrics[1].get('field_ref', ''))
    x_info = columns_by_id.get(x_ref)
    y_info = columns_by_id.get(y_ref)
    x_name = x_info.name if x_info else f"Col #{x_ref}"
    y_name = y_info.name if y_info else f"Col #{y_ref}"

    x_series = pd.to_numeric(df.get(x_ref), errors='coerce')
    y_series = pd.to_numeric(df.get(y_ref), errors='coerce')

    # Drop rows where either axis is NaN
    valid_mask = x_series.notna() & y_series.notna()
    x_vals = x_series[valid_mask].tolist()
    y_vals = y_series[valid_mask].tolist()

    limit = options.get('limit', 500)
    if len(x_vals) > limit:
        x_vals = x_vals[:limit]
        y_vals = y_vals[:limit]
        result.warnings.append(f"Puntos limitados a {limit}.")

    result.columns = [
        {'key': 'x', 'label': x_name, 'type': 'metric'},
        {'key': 'y', 'label': y_name, 'type': 'metric'},
    ]
    result.rows = [
        {'x': _serialize_value(x_vals[i]), 'y': _serialize_value(y_vals[i])}
        for i in range(len(x_vals))
    ]

    result.chart_data = {
        'type': 'scatter',
        'data': {
            'datasets': [{
                'label': f'{x_name} vs {y_name}',
                'data': [{'x': x_vals[i], 'y': y_vals[i]} for i in range(len(x_vals))],
            }],
        },
    }

    return result


def _aggregate_single(df_or_group, col_ref, agg_func):
    """Compute a single aggregation on a column."""
    if col_ref not in df_or_group.columns:
        return 0

    series = df_or_group[col_ref]

    if agg_func == 'count':
        return int(series.count())
    elif agg_func == 'distinct_count':
        return int(series.nunique())
    elif agg_func == 'sum':
        val = pd.to_numeric(series, errors='coerce').sum()
        return round(float(val), 4) if not pd.isna(val) else 0
    elif agg_func == 'avg':
        val = pd.to_numeric(series, errors='coerce').mean()
        return round(float(val), 4) if not pd.isna(val) else 0
    elif agg_func == 'min':
        val = series.dropna().min() if not series.dropna().empty else None
        return _serialize_value(val)
    elif agg_func == 'max':
        val = series.dropna().max() if not series.dropna().empty else None
        return _serialize_value(val)
    else:
        return 0


def _serialize_value(val):
    """Convert a value to a JSON-safe representation."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.isoformat()
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return round(float(val), 4)
    if isinstance(val, pd.Period):
        return str(val)
    return val


def _build_bar_pie_chart(widget_type, result):
    """Build Chart.js-compatible data from aggregated result rows."""
    if not result.rows or not result.columns:
        return {}

    # Find dimension and metric columns
    dim_cols = [c for c in result.columns if c['type'] == 'dimension']
    met_cols = [c for c in result.columns if c['type'] == 'metric']

    if not dim_cols:
        return {}

    labels = [str(row.get(dim_cols[0]['key'], '')) for row in result.rows]

    datasets = []
    for met in met_cols:
        data = [row.get(met['key'], 0) for row in result.rows]
        datasets.append({
            'label': met['label'],
            'data': data,
        })

    chart_type = 'bar' if widget_type == 'bar' else 'pie'

    return {
        'type': chart_type,
        'data': {
            'labels': labels,
            'datasets': datasets,
        },
    }
