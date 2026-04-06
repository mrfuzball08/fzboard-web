"""
Import mapping service — suggests header mappings between uploaded file columns
and template column definitions.
"""

from difflib import SequenceMatcher


def suggest_mapping(file_headers, template_columns):
    """
    Suggest a mapping from file headers to template columns.

    Uses a three-pass strategy:
    1. Exact match (case-sensitive)
    2. Case-insensitive match
    3. Fuzzy partial match (>= 0.6 similarity)

    Args:
        file_headers: list[str] — column names from the uploaded file.
        template_columns: QuerySet or list of TemplateColumn objects with .id and .name.

    Returns:
        dict with:
            'mapping': dict[str, int|None] — file header → TemplateColumn.id (None if unmapped)
            'extra_columns': list[str] — file headers not mapped to any template column
            'missing_columns': list[dict] — template columns not covered by any file header
    """
    # Build lookup structures
    col_by_name = {}         # exact match
    col_by_lower = {}        # case-insensitive match
    col_list = []            # for fuzzy matching

    for tc in template_columns:
        col_by_name[tc.name] = tc
        col_by_lower[tc.name.lower().strip()] = tc
        col_list.append(tc)

    mapping = {}
    matched_col_ids = set()

    # Pass 1: Exact match
    for header in file_headers:
        if header in col_by_name and col_by_name[header].id not in matched_col_ids:
            tc = col_by_name[header]
            mapping[header] = tc.id
            matched_col_ids.add(tc.id)

    # Pass 2: Case-insensitive match for remaining headers
    for header in file_headers:
        if header in mapping:
            continue
        key = header.lower().strip()
        if key in col_by_lower and col_by_lower[key].id not in matched_col_ids:
            tc = col_by_lower[key]
            mapping[header] = tc.id
            matched_col_ids.add(tc.id)

    # Pass 3: Fuzzy match for remaining headers
    for header in file_headers:
        if header in mapping:
            continue
        best_score = 0.0
        best_tc = None
        for tc in col_list:
            if tc.id in matched_col_ids:
                continue
            score = SequenceMatcher(None, header.lower().strip(), tc.name.lower().strip()).ratio()
            if score > best_score and score >= 0.6:
                best_score = score
                best_tc = tc

        if best_tc:
            mapping[header] = best_tc.id
            matched_col_ids.add(best_tc.id)
        else:
            mapping[header] = None

    # Identify extra columns (file headers not mapped)
    extra_columns = [h for h in file_headers if mapping.get(h) is None]

    # Identify missing columns (template columns not covered)
    missing_columns = [
        {'id': tc.id, 'name': tc.name, 'data_type': tc.data_type}
        for tc in col_list
        if tc.id not in matched_col_ids
    ]

    return {
        'mapping': mapping,
        'extra_columns': extra_columns,
        'missing_columns': missing_columns,
    }
