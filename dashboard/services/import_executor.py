"""
Import executor service — orchestrates the full import pipeline.
Handles replace/append modes with transactional safety.
"""

from django.db import transaction
from django.utils import timezone

from dashboard.models import Dataset, DatasetImport, DatasetRow, DatasetCellIssue
from dashboard.services.import_validation import validate_row


def execute_import(dataset, dataframe, header_mapping, mode, dataset_import):
    """
    Execute a data import into a dataset.

    This function:
    1. Updates the dataset status to 'importing'
    2. In replace mode: deletes existing rows (inside a transaction)
    3. Validates and saves each row
    4. Creates DatasetCellIssue records for invalid cells
    5. Updates counts on the DatasetImport and Dataset

    Args:
        dataset: Dataset instance
        dataframe: pandas DataFrame with the imported data
        header_mapping: dict mapping file header (str) → TemplateColumn.id (int or None)
        mode: 'replace' or 'append'
        dataset_import: DatasetImport instance (already created with status='pending')

    Returns:
        DatasetImport: The updated import record.
    """
    # Build template column lookup
    template_columns = dataset.template.columns.all()
    template_columns_by_id = {tc.id: tc for tc in template_columns}

    # Identify extra and missing columns
    extra_columns = [h for h, col_id in header_mapping.items() if col_id is None]
    mapped_col_ids = {col_id for col_id in header_mapping.values() if col_id is not None}
    missing_columns = [
        tc.name for tc in template_columns if tc.id not in mapped_col_ids
    ]

    try:
        with transaction.atomic():
            # Update import status
            dataset_import.status = 'processing'
            dataset_import.extra_columns_json = extra_columns
            dataset_import.missing_columns_json = missing_columns
            dataset_import.save(update_fields=[
                'status', 'extra_columns_json', 'missing_columns_json'
            ])

            # Update dataset status
            dataset.status = 'importing'
            dataset.save(update_fields=['status'])

            # Replace mode: delete existing rows
            if mode == 'replace':
                DatasetRow.objects.filter(dataset=dataset).delete()

            # Process rows
            total_rows = 0
            inserted_rows = 0
            invalid_rows = 0

            # Determine starting row index
            if mode == 'append':
                existing_max = DatasetRow.objects.filter(
                    dataset=dataset
                ).order_by('-row_index').values_list('row_index', flat=True).first()
                start_index = (existing_max or 0) + 1
            else:
                start_index = 1

            # Bulk prepare rows and issues
            rows_to_create = []
            issues_to_create = []

            for idx, (_, df_row) in enumerate(dataframe.iterrows()):
                total_rows += 1
                row_index = start_index + idx

                # Build row data dict from DataFrame row
                row_data = {}
                for col_name in dataframe.columns:
                    val = df_row[col_name]
                    row_data[str(col_name).strip()] = val if val != '' else None

                # Validate row
                data_json, row_issues = validate_row(
                    row_data, header_mapping, template_columns_by_id
                )

                is_valid = len(row_issues) == 0
                if not is_valid:
                    invalid_rows += 1

                row_obj = DatasetRow(
                    dataset=dataset,
                    dataset_import=dataset_import,
                    row_index=row_index,
                    data_json=data_json,
                    is_valid=is_valid,
                    issue_count=len(row_issues),
                )
                rows_to_create.append((row_obj, row_issues))
                inserted_rows += 1

            # Bulk create rows
            created_rows = DatasetRow.objects.bulk_create(
                [r for r, _ in rows_to_create]
            )

            # Create issues with proper row FK references
            for created_row, (_, row_issues) in zip(created_rows, rows_to_create):
                for issue_data in row_issues:
                    issues_to_create.append(DatasetCellIssue(
                        dataset_row=created_row,
                        template_column_id=issue_data['template_column_id'],
                        raw_value=issue_data['raw_value'],
                        issue_code=issue_data['issue_code'],
                        message=issue_data['message'],
                    ))

            if issues_to_create:
                DatasetCellIssue.objects.bulk_create(issues_to_create)

            # Update DatasetImport counts
            dataset_import.total_rows = total_rows
            dataset_import.inserted_rows = inserted_rows
            dataset_import.invalid_rows = invalid_rows
            dataset_import.status = 'completed'
            dataset_import.save(update_fields=[
                'total_rows', 'inserted_rows', 'invalid_rows', 'status'
            ])

            # Update Dataset counts
            dataset.row_count = DatasetRow.objects.filter(dataset=dataset).count()
            dataset.invalid_row_count = DatasetRow.objects.filter(
                dataset=dataset, is_valid=False
            ).count()
            dataset.status = 'ready'
            dataset.last_imported_at = timezone.now()
            dataset.save(update_fields=[
                'row_count', 'invalid_row_count', 'status', 'last_imported_at'
            ])

    except Exception as e:
        # If anything fails, mark both as failed
        dataset_import.status = 'failed'
        dataset_import.save(update_fields=['status'])
        dataset.status = 'failed'
        dataset.save(update_fields=['status'])
        raise e

    return dataset_import
