"""
Import validation service — validates cell values against template column data types.
"""

import re
from datetime import datetime


# ──────────────────────────────────────────────
#  Canonical boolean values
# ──────────────────────────────────────────────
BOOLEAN_TRUE = {'true', 'yes', 'si', 'sí', '1', 'verdadero', 'v'}
BOOLEAN_FALSE = {'false', 'no', '0', 'falso', 'f'}
BOOLEAN_ALL = BOOLEAN_TRUE | BOOLEAN_FALSE

# ──────────────────────────────────────────────
#  Email and URL regex patterns
# ──────────────────────────────────────────────
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)
URL_REGEX = re.compile(
    r'^https?://[^\s/$.?#].[^\s]*$',
    re.IGNORECASE
)

# ──────────────────────────────────────────────
#  Supported date formats
# ──────────────────────────────────────────────
DATE_FORMATS = [
    '%Y-%m-%d',       # 2026-04-01
    '%d/%m/%Y',       # 01/04/2026
    '%m/%d/%Y',       # 04/01/2026
    '%d-%m-%Y',       # 01-04-2026
    '%Y/%m/%d',       # 2026/04/01
    '%d %b %Y',       # 01 Apr 2026
    '%d %B %Y',       # 01 April 2026
    '%Y-%m-%dT%H:%M:%S',  # ISO 8601
]


def validate_cell(value, data_type):
    """
    Validate a single cell value against a data type.

    Args:
        value: The raw string value (or None/'').
        data_type: One of the TemplateColumn.DATA_TYPE_CHOICES keys.

    Returns:
        tuple: (cleaned_value: str|None, issue_code: str|None, message: str|None)
            - If valid: (cleaned_value, None, None)
            - If invalid: (raw_value, issue_code, message)
    """
    # Handle missing/empty values
    if value is None or (isinstance(value, str) and value.strip() == ''):
        return (None, 'missing_value', 'Valor vacío o faltante')

    raw = str(value).strip()

    if data_type == 'text':
        return (raw, None, None)

    if data_type == 'integer':
        return _validate_integer(raw)

    if data_type == 'float':
        return _validate_float(raw)

    if data_type == 'date':
        return _validate_date(raw)

    if data_type == 'boolean':
        return _validate_boolean(raw)

    if data_type == 'email':
        return _validate_email(raw)

    if data_type == 'url':
        return _validate_url(raw)

    # Unknown type — treat as text
    return (raw, None, None)


def _validate_integer(raw):
    """Validate an integer value."""
    try:
        # Allow float-like strings that are whole numbers (e.g. "42.0")
        val = float(raw)
        if val == int(val):
            return (str(int(val)), None, None)
        return (raw, 'invalid_integer', f'"{raw}" no es un número entero válido')
    except (ValueError, OverflowError):
        return (raw, 'invalid_integer', f'"{raw}" no es un número entero válido')


def _validate_float(raw):
    """Validate a decimal/float value."""
    try:
        float(raw)
        return (raw, None, None)
    except (ValueError, OverflowError):
        return (raw, 'invalid_float', f'"{raw}" no es un número decimal válido')


def _validate_date(raw):
    """Validate a date value against supported formats."""
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt)
            # Normalize to ISO format
            return (parsed.strftime('%Y-%m-%d'), None, None)
        except ValueError:
            continue
    return (raw, 'invalid_date', f'"{raw}" no es una fecha válida')


def _validate_boolean(raw):
    """Validate a boolean value against canonical values."""
    if raw.lower().strip() in BOOLEAN_ALL:
        normalized = 'true' if raw.lower().strip() in BOOLEAN_TRUE else 'false'
        return (normalized, None, None)
    return (raw, 'invalid_boolean', f'"{raw}" no es un valor booleano válido (use true/false, si/no, 1/0)')


def _validate_email(raw):
    """Validate an email address format."""
    if EMAIL_REGEX.match(raw):
        return (raw, None, None)
    return (raw, 'invalid_email', f'"{raw}" no es un correo electrónico válido')


def _validate_url(raw):
    """Validate a URL format."""
    if URL_REGEX.match(raw):
        return (raw, None, None)
    return (raw, 'invalid_url', f'"{raw}" no es una URL válida')


def validate_row(row_data, header_mapping, template_columns_by_id):
    """
    Validate all cells in a row.

    Args:
        row_data: dict mapping file header → raw value from the DataFrame row.
        header_mapping: dict mapping file header → TemplateColumn.id (int or None).
        template_columns_by_id: dict mapping TemplateColumn.id → TemplateColumn object.

    Returns:
        tuple: (data_json: dict, issues: list[dict])
            - data_json: keys are str(TemplateColumn.id), values are cleaned strings or None.
            - issues: list of dicts with keys: template_column_id, raw_value, issue_code, message
    """
    data_json = {}
    issues = []
    mapped_col_ids = set()

    # Process mapped columns
    for file_header, col_id in header_mapping.items():
        if col_id is None:
            continue
        mapped_col_ids.add(col_id)
        tc = template_columns_by_id.get(col_id)
        if tc is None:
            continue

        raw_value = row_data.get(file_header)
        cleaned, issue_code, message = validate_cell(raw_value, tc.data_type)
        data_json[str(col_id)] = cleaned

        if issue_code:
            issues.append({
                'template_column_id': col_id,
                'raw_value': str(raw_value) if raw_value is not None else None,
                'issue_code': issue_code,
                'message': message,
            })

    # Check for missing template columns (not covered by any mapping)
    for col_id, tc in template_columns_by_id.items():
        if col_id not in mapped_col_ids:
            data_json[str(col_id)] = None
            issues.append({
                'template_column_id': col_id,
                'raw_value': None,
                'issue_code': 'missing_column',
                'message': f'Columna "{tc.name}" no está mapeada en el archivo',
            })

    return data_json, issues
