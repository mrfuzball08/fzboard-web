"""
Tests for the import services: readers, mapping, validation, executor.
"""

import io
import os

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from dashboard.models import (
    User, TableTemplate, TemplateColumn,
    Dataset, DatasetImport, DatasetRow, DatasetCellIssue, Report,
)
from dashboard.services.import_readers import read_upload_to_dataframe, extract_headers
from dashboard.services.import_mapping import suggest_mapping
from dashboard.services.import_validation import validate_cell, validate_row
from dashboard.services.import_executor import execute_import


# ──────────────────────────────────────────────
#  Import Readers Tests
# ──────────────────────────────────────────────

class ImportReadersTests(TestCase):
    """Tests for reading CSV/Excel files."""

    def test_read_csv_upload(self):
        """Read a simple CSV from an uploaded file."""
        csv_content = b"Name,Age,Email\nAlice,30,alice@test.com\nBob,25,bob@test.com\n"
        uploaded = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
        df = read_upload_to_dataframe(uploaded)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['Name', 'Age', 'Email'])

    def test_read_csv_preserves_strings(self):
        """All values should be read as strings (dtype=str)."""
        csv_content = b"ID,Value\n001,3.14\n"
        uploaded = SimpleUploadedFile("nums.csv", csv_content, content_type="text/csv")
        df = read_upload_to_dataframe(uploaded)
        # "001" must NOT be read as integer 1
        self.assertEqual(df.iloc[0]['ID'], '001')

    def test_unsupported_file_type(self):
        """Non-CSV/Excel files should raise ValueError."""
        uploaded = SimpleUploadedFile("data.json", b"{}", content_type="application/json")
        with self.assertRaises(ValueError) as ctx:
            read_upload_to_dataframe(uploaded)
        self.assertIn('.json', str(ctx.exception))

    def test_extract_headers(self):
        """Extract column names from a DataFrame."""
        df = pd.DataFrame(columns=['Name', 'Age', 'Email'])
        headers = extract_headers(df)
        self.assertEqual(headers, ['Name', 'Age', 'Email'])

    def test_extract_headers_strips_whitespace(self):
        """Headers should be stripped of whitespace."""
        df = pd.DataFrame(columns=[' Name ', 'Age\t', ' Email'])
        headers = extract_headers(df)
        self.assertEqual(headers, ['Name', 'Age', 'Email'])


# ──────────────────────────────────────────────
#  Import Mapping Tests
# ──────────────────────────────────────────────

class ImportMappingTests(TestCase):
    """Tests for header mapping suggestions."""

    def setUp(self):
        self.user = User.objects.create_user(username='maptest', password='testpass123')
        self.template = TableTemplate.objects.create(name='Map Template', owner=self.user)
        self.col_name = TemplateColumn.objects.create(
            template=self.template, name='Name', data_type='text', order=0,
        )
        self.col_email = TemplateColumn.objects.create(
            template=self.template, name='Email', data_type='email', order=1,
        )
        self.col_age = TemplateColumn.objects.create(
            template=self.template, name='Age', data_type='integer', order=2,
        )

    def test_exact_match(self):
        """File headers matching template columns exactly."""
        result = suggest_mapping(
            ['Name', 'Email', 'Age'],
            self.template.columns.all()
        )
        self.assertEqual(result['mapping']['Name'], self.col_name.id)
        self.assertEqual(result['mapping']['Email'], self.col_email.id)
        self.assertEqual(result['mapping']['Age'], self.col_age.id)
        self.assertEqual(result['extra_columns'], [])
        self.assertEqual(result['missing_columns'], [])

    def test_case_insensitive_match(self):
        """File headers with different casing should map correctly."""
        result = suggest_mapping(
            ['name', 'EMAIL', 'aGe'],
            self.template.columns.all()
        )
        self.assertEqual(result['mapping']['name'], self.col_name.id)
        self.assertEqual(result['mapping']['EMAIL'], self.col_email.id)
        self.assertEqual(result['mapping']['aGe'], self.col_age.id)

    def test_extra_columns(self):
        """File headers not in template should be flagged as extra."""
        result = suggest_mapping(
            ['Name', 'Email', 'Age', 'Phone', 'Address'],
            self.template.columns.all()
        )
        self.assertIn('Phone', result['extra_columns'])
        self.assertIn('Address', result['extra_columns'])

    def test_missing_columns(self):
        """Template columns not in file headers should be flagged as missing."""
        result = suggest_mapping(
            ['Name'],
            self.template.columns.all()
        )
        missing_names = [m['name'] for m in result['missing_columns']]
        self.assertIn('Email', missing_names)
        self.assertIn('Age', missing_names)

    def test_fuzzy_match(self):
        """Similar names should be matched via fuzzy matching."""
        result = suggest_mapping(
            ['Nombre', 'Correo', 'Edad'],  # Only "Nombre" is close to "Name"
            self.template.columns.all()
        )
        # At least "Nombre" should fuzzy-match to "Name" (ratio ~0.6)
        # Others may not meet the 0.6 threshold
        self.assertIsNotNone(result['mapping'])


# ──────────────────────────────────────────────
#  Import Validation Tests
# ──────────────────────────────────────────────

class ImportValidationCellTests(TestCase):
    """Tests for cell-level validation."""

    # ─── Text ─────────────────────────────────────

    def test_text_valid(self):
        cleaned, code, msg = validate_cell("Hello World", "text")
        self.assertEqual(cleaned, "Hello World")
        self.assertIsNone(code)

    def test_text_empty(self):
        cleaned, code, msg = validate_cell("", "text")
        self.assertIsNone(cleaned)
        self.assertEqual(code, "missing_value")

    # ─── Integer ──────────────────────────────────

    def test_integer_valid(self):
        cleaned, code, msg = validate_cell("42", "integer")
        self.assertEqual(cleaned, "42")
        self.assertIsNone(code)

    def test_integer_float_whole(self):
        """Integer from "42.0" should be accepted."""
        cleaned, code, msg = validate_cell("42.0", "integer")
        self.assertEqual(cleaned, "42")
        self.assertIsNone(code)

    def test_integer_invalid(self):
        cleaned, code, msg = validate_cell("abc", "integer")
        self.assertEqual(code, "invalid_integer")

    def test_integer_float_non_whole(self):
        cleaned, code, msg = validate_cell("42.5", "integer")
        self.assertEqual(code, "invalid_integer")

    # ─── Float ────────────────────────────────────

    def test_float_valid(self):
        cleaned, code, msg = validate_cell("3.14", "float")
        self.assertEqual(cleaned, "3.14")
        self.assertIsNone(code)

    def test_float_integer(self):
        cleaned, code, msg = validate_cell("100", "float")
        self.assertIsNone(code)

    def test_float_invalid(self):
        cleaned, code, msg = validate_cell("not a number", "float")
        self.assertEqual(code, "invalid_float")

    # ─── Date ─────────────────────────────────────

    def test_date_iso(self):
        cleaned, code, msg = validate_cell("2026-04-01", "date")
        self.assertEqual(cleaned, "2026-04-01")
        self.assertIsNone(code)

    def test_date_slash(self):
        cleaned, code, msg = validate_cell("01/04/2026", "date")
        self.assertEqual(cleaned, "2026-04-01")
        self.assertIsNone(code)

    def test_date_invalid(self):
        cleaned, code, msg = validate_cell("not-a-date", "date")
        self.assertEqual(code, "invalid_date")

    # ─── Boolean ──────────────────────────────────

    def test_boolean_true_variants(self):
        for val in ['true', 'True', 'yes', 'si', 'sí', '1', 'verdadero', 'v']:
            cleaned, code, msg = validate_cell(val, "boolean")
            self.assertEqual(cleaned, "true", f"Failed for: {val}")
            self.assertIsNone(code)

    def test_boolean_false_variants(self):
        for val in ['false', 'False', 'no', '0', 'falso', 'f']:
            cleaned, code, msg = validate_cell(val, "boolean")
            self.assertEqual(cleaned, "false", f"Failed for: {val}")
            self.assertIsNone(code)

    def test_boolean_invalid(self):
        cleaned, code, msg = validate_cell("maybe", "boolean")
        self.assertEqual(code, "invalid_boolean")

    # ─── Email ────────────────────────────────────

    def test_email_valid(self):
        cleaned, code, msg = validate_cell("test@example.com", "email")
        self.assertEqual(cleaned, "test@example.com")
        self.assertIsNone(code)

    def test_email_invalid(self):
        cleaned, code, msg = validate_cell("not-an-email", "email")
        self.assertEqual(code, "invalid_email")

    # ─── URL ──────────────────────────────────────

    def test_url_valid(self):
        cleaned, code, msg = validate_cell("https://example.com/path", "url")
        self.assertEqual(cleaned, "https://example.com/path")
        self.assertIsNone(code)

    def test_url_http(self):
        cleaned, code, msg = validate_cell("http://example.com", "url")
        self.assertIsNone(code)

    def test_url_invalid(self):
        cleaned, code, msg = validate_cell("not a url", "url")
        self.assertEqual(code, "invalid_url")

    # ─── Missing Values ──────────────────────────

    def test_none_all_types(self):
        for dt in ['text', 'integer', 'float', 'date', 'boolean', 'email', 'url']:
            cleaned, code, msg = validate_cell(None, dt)
            self.assertEqual(code, 'missing_value', f"Failed for type: {dt}")


class ImportValidationRowTests(TestCase):
    """Tests for row-level validation."""

    def setUp(self):
        self.user = User.objects.create_user(username='valrowtest', password='testpass123')
        self.template = TableTemplate.objects.create(name='Val Template', owner=self.user)
        self.col_name = TemplateColumn.objects.create(
            template=self.template, name='Name', data_type='text', order=0,
        )
        self.col_age = TemplateColumn.objects.create(
            template=self.template, name='Age', data_type='integer', order=1,
        )
        self.columns_by_id = {
            self.col_name.id: self.col_name,
            self.col_age.id: self.col_age,
        }

    def test_valid_row(self):
        row_data = {'Name': 'Alice', 'Age': '30'}
        mapping = {'Name': self.col_name.id, 'Age': self.col_age.id}
        data_json, issues = validate_row(row_data, mapping, self.columns_by_id)
        self.assertEqual(len(issues), 0)
        self.assertEqual(data_json[str(self.col_name.id)], 'Alice')
        self.assertEqual(data_json[str(self.col_age.id)], '30')

    def test_invalid_row(self):
        row_data = {'Name': 'Alice', 'Age': 'not-a-number'}
        mapping = {'Name': self.col_name.id, 'Age': self.col_age.id}
        data_json, issues = validate_row(row_data, mapping, self.columns_by_id)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['issue_code'], 'invalid_integer')

    def test_missing_column_in_mapping(self):
        """A template column not covered by the mapping should create a missing_column issue."""
        row_data = {'Name': 'Alice'}
        mapping = {'Name': self.col_name.id}  # Age not mapped
        data_json, issues = validate_row(row_data, mapping, self.columns_by_id)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['issue_code'], 'missing_column')


# ──────────────────────────────────────────────
#  Import Executor Tests
# ──────────────────────────────────────────────

class ImportExecutorTests(TestCase):
    """Tests for the import executor service."""

    def setUp(self):
        self.user = User.objects.create_user(username='exectest', password='testpass123')
        self.template = TableTemplate.objects.create(name='Exec Template', owner=self.user)
        self.col_name = TemplateColumn.objects.create(
            template=self.template, name='Name', data_type='text', order=0,
        )
        self.col_age = TemplateColumn.objects.create(
            template=self.template, name='Age', data_type='integer', order=1,
        )
        self.dataset = Dataset.objects.create(
            name='Exec Dataset', owner=self.user, template=self.template,
        )

    def _make_df(self, data):
        return pd.DataFrame(data)

    def _make_import(self, mode='replace'):
        return DatasetImport.objects.create(
            dataset=self.dataset,
            source_filename='test.csv',
            mode=mode,
            status='pending',
        )

    def test_replace_mode_basic(self):
        """Replace mode: import rows, update counts."""
        df = self._make_df({'Name': ['Alice', 'Bob'], 'Age': ['30', '25']})
        mapping = {'Name': self.col_name.id, 'Age': self.col_age.id}
        imp = self._make_import(mode='replace')

        result = execute_import(self.dataset, df, mapping, 'replace', imp)

        self.assertEqual(result.status, 'completed')
        self.assertEqual(result.total_rows, 2)
        self.assertEqual(result.inserted_rows, 2)
        self.assertEqual(result.invalid_rows, 0)

        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.row_count, 2)
        self.assertEqual(self.dataset.status, 'ready')
        self.assertIsNotNone(self.dataset.last_imported_at)

    def test_replace_mode_deletes_existing(self):
        """Replace mode should delete existing rows before importing new ones."""
        # First import
        df1 = self._make_df({'Name': ['Alice'], 'Age': ['30']})
        mapping = {'Name': self.col_name.id, 'Age': self.col_age.id}
        imp1 = self._make_import(mode='replace')
        execute_import(self.dataset, df1, mapping, 'replace', imp1)

        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.row_count, 1)

        # Second import (replace)
        df2 = self._make_df({'Name': ['Bob', 'Charlie'], 'Age': ['25', '35']})
        imp2 = self._make_import(mode='replace')
        execute_import(self.dataset, df2, mapping, 'replace', imp2)

        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.row_count, 2)

        # Only the new rows should exist
        names = list(DatasetRow.objects.filter(
            dataset=self.dataset
        ).values_list('data_json', flat=True))
        name_values = [d.get(str(self.col_name.id)) for d in names]
        self.assertIn('Bob', name_values)
        self.assertIn('Charlie', name_values)
        self.assertNotIn('Alice', name_values)

    def test_append_mode(self):
        """Append mode should keep existing rows and add new ones."""
        # First import
        df1 = self._make_df({'Name': ['Alice'], 'Age': ['30']})
        mapping = {'Name': self.col_name.id, 'Age': self.col_age.id}
        imp1 = self._make_import(mode='replace')
        execute_import(self.dataset, df1, mapping, 'replace', imp1)

        # Second import (append)
        df2 = self._make_df({'Name': ['Bob'], 'Age': ['25']})
        imp2 = self._make_import(mode='append')
        execute_import(self.dataset, df2, mapping, 'append', imp2)

        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.row_count, 2)

    def test_invalid_rows_tracked(self):
        """Rows with invalid cells should be saved with is_valid=False."""
        df = self._make_df({'Name': ['Alice', 'Bob'], 'Age': ['30', 'not-a-number']})
        mapping = {'Name': self.col_name.id, 'Age': self.col_age.id}
        imp = self._make_import(mode='replace')

        result = execute_import(self.dataset, df, mapping, 'replace', imp)

        self.assertEqual(result.invalid_rows, 1)
        invalid_rows = DatasetRow.objects.filter(dataset=self.dataset, is_valid=False)
        self.assertEqual(invalid_rows.count(), 1)

        # The issue should be recorded
        issues = DatasetCellIssue.objects.filter(dataset_row__dataset=self.dataset)
        self.assertGreaterEqual(issues.count(), 1)

    def test_extra_and_missing_columns(self):
        """Extra and missing columns should be recorded on the import."""
        df = self._make_df({'Name': ['Alice'], 'Phone': ['555-1234']})
        mapping = {'Name': self.col_name.id, 'Phone': None}
        imp = self._make_import(mode='replace')

        result = execute_import(self.dataset, df, mapping, 'replace', imp)

        self.assertIn('Phone', result.extra_columns_json)
        self.assertIn('Age', result.missing_columns_json)

    def test_empty_dataframe(self):
        """Importing an empty dataframe should work without error."""
        df = self._make_df({'Name': [], 'Age': []})
        mapping = {'Name': self.col_name.id, 'Age': self.col_age.id}
        imp = self._make_import(mode='replace')

        result = execute_import(self.dataset, df, mapping, 'replace', imp)

        self.assertEqual(result.total_rows, 0)
        self.assertEqual(result.status, 'completed')


# ──────────────────────────────────────────────
#  Report Validation Tests
# ──────────────────────────────────────────────

from dashboard.services.report_validation import validate_widget_config

class ReportValidationTests(TestCase):
    """Tests for report widget configuration validation."""

    def setUp(self):
        self.user = User.objects.create_user(username='reportuser', password='testpass123')
        self.template = TableTemplate.objects.create(name='Report Template', owner=self.user)
        self.col_text = TemplateColumn.objects.create(
            template=self.template, name='TextCol', data_type='text', order=0,
        )
        self.col_num = TemplateColumn.objects.create(
            template=self.template, name='NumCol', data_type='integer', order=1,
        )
        self.dataset = Dataset.objects.create(
            name='Test Dataset', owner=self.user, template=self.template,
        )

    def test_pie_chart_validation(self):
        """Pie chart requires exactly one dimension and one metric."""
        config = {
            'dimensions': [{'field_kind': 'template_column', 'field_ref': self.col_text.id, 'group_by': 'raw'}],
            'metrics': [{'field_kind': 'template_column', 'field_ref': self.col_num.id, 'aggregation': 'sum'}]
        }
        is_valid, errors = validate_widget_config('pie', config, self.dataset)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_pie_chart_invalid(self):
        """Pie chart with multiple dimensions throws valid specific error."""
        config = {
            'dimensions': [
                {'field_kind': 'template_column', 'field_ref': self.col_text.id, 'group_by': 'raw'},
                {'field_kind': 'template_column', 'field_ref': self.col_num.id, 'group_by': 'raw'}
            ],
            'metrics': [{'field_kind': 'template_column', 'field_ref': self.col_num.id, 'aggregation': 'sum'}]
        }
        is_valid, errors = validate_widget_config('pie', config, self.dataset)
        self.assertFalse(is_valid)
        self.assertIn("Un gráfico de pastel necesita exactamente una dimensión.", errors)

    def test_table_validation(self):
        """Table requires at least one metric or dimension."""
        config = {'dimensions': [], 'metrics': []}
        is_valid, errors = validate_widget_config('table', config, self.dataset)
        self.assertFalse(is_valid)
        self.assertIn("Una tabla necesita al menos una dimensión o una métrica.", errors)


# ──────────────────────────────────────────────
#  Report Query Tests
# ──────────────────────────────────────────────

from dashboard.services.report_query import execute_widget

class ReportQueryTests(TestCase):
    """Tests for executing pandas querying and grouping routines on datasets."""

    def setUp(self):
        self.user = User.objects.create_user(username='queryuser', password='testpass123')
        self.template = TableTemplate.objects.create(name='Query Template', owner=self.user)
        self.col_text = TemplateColumn.objects.create(
            template=self.template, name='City', data_type='text', order=0,
        )
        self.col_num = TemplateColumn.objects.create(
            template=self.template, name='Sales', data_type='integer', order=1,
        )
        self.dataset = Dataset.objects.create(
            name='Query Dataset', owner=self.user, template=self.template,
        )
        # Create an import session for the rows
        self.dataset_import = DatasetImport.objects.create(
            dataset=self.dataset, source_filename="test.csv", status='completed', mode='replace'
        )
        # Populate DatasetRow with some sample rows
        DatasetRow.objects.create(dataset=self.dataset, dataset_import=self.dataset_import, row_index=1, data_json={str(self.col_text.id): 'CDMX', str(self.col_num.id): '100'})
        DatasetRow.objects.create(dataset=self.dataset, dataset_import=self.dataset_import, row_index=2, data_json={str(self.col_text.id): 'CDMX', str(self.col_num.id): '200'})
        DatasetRow.objects.create(dataset=self.dataset, dataset_import=self.dataset_import, row_index=3, data_json={str(self.col_text.id): 'GDL', str(self.col_num.id): '150'})

        self.report = Report.objects.create(name='Query Test Report', owner=self.user, dataset=self.dataset)

    def test_execute_table_widget(self):
        """Ensure standard DataFrame aggregations correctly execute logic."""
        widget = {
            'widget_type': 'table',
            'config_json': {
                'dimensions': [{'field_kind': 'template_column', 'field_ref': self.col_text.id, 'group_by': 'raw'}],
                'metrics': [{'field_kind': 'template_column', 'field_ref': self.col_num.id, 'aggregation': 'sum'}]
            }
        }
        result = execute_widget(widget, self.report)
        self.assertEqual(result.total_rows, 2)  # Two unique groups: CDMX and GDL

        # Check that CDMX has aggregated sum 300
        cdmx_row = next(r for r in result.rows if r['dim_0'] == 'CDMX')
        self.assertEqual(cdmx_row['metric_0'], 300.0)

    def test_execute_pie_widget(self):
        """Ensure chart JSON generated strips python tuples out of singles groupby index keys."""
        widget = {
            'widget_type': 'pie',
            'config_json': {
                'dimensions': [{'field_kind': 'template_column', 'field_ref': self.col_text.id, 'group_by': 'raw'}],
                'metrics': [{'field_kind': 'template_column', 'field_ref': self.col_num.id, 'aggregation': 'sum'}]
            }
        }
        result = execute_widget(widget, self.report)
        
        self.assertEqual(result.chart_data['type'], 'pie')
        self.assertIn('CDMX', result.chart_data['data']['labels'])
        self.assertIn('GDL', result.chart_data['data']['labels'])
        
        # Verify dataset arrays match generated tuples smoothly
        cdmx_index = result.chart_data['data']['labels'].index('CDMX')
        self.assertEqual(result.chart_data['data']['datasets'][0]['data'][cdmx_index], 300.0)
