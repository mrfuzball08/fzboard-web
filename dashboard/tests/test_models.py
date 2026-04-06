import time

from django.test import TestCase

from dashboard.models import (
    User, TableTemplate, TemplateColumn,
    Dataset, DatasetImport, DatasetRow, DatasetCellIssue,
)


class UserModelTests(TestCase):
    """Tests for the User model."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@fzboard.test', password='testpass123',
        )
        self.user1 = User.objects.create_user(
            username='alice', email='alice@fzboard.test', password='testpass123',
            first_name='Alice', last_name='Wonderland',
        )
        self.user2 = User.objects.create_user(
            username='bob', email='bob@fzboard.test', password='testpass123',
            first_name='Bob', last_name='Builder',
        )

    def test_user_creation(self):
        """Verify that the test users were created correctly."""
        self.assertEqual(User.objects.count(), 3)

    def test_list_all_users(self):
        """Fetch all users and verify the list."""
        usernames = list(User.objects.values_list('username', flat=True))
        self.assertIn('admin', usernames)
        self.assertIn('alice', usernames)
        self.assertIn('bob', usernames)

    def test_user_str(self):
        """Verify the string representation of a user."""
        self.assertEqual(str(self.user1), 'alice')

    def test_list_users_response_time(self):
        """Measure user list query time."""
        start = time.perf_counter()
        users = list(User.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF] User list query: {elapsed:.4f}s ({len(users)} users)")
        self.assertLess(elapsed, 1.0)


class TemplateModelTests(TestCase):
    """Tests for the TableTemplate and TemplateColumn models."""

    def setUp(self):
        self.user = User.objects.create_user(username='modeltest', password='testpass123')
        self.template = TableTemplate.objects.create(
            name='Test Template', description='A test template', owner=self.user,
        )
        self.col1 = TemplateColumn.objects.create(
            template=self.template, name='Name', data_type='text', order=0,
        )
        self.col2 = TemplateColumn.objects.create(
            template=self.template, name='Age', data_type='integer', order=1,
        )

    def test_template_str(self):
        self.assertEqual(str(self.template), 'Test Template')

    def test_column_str(self):
        self.assertEqual(str(self.col1), 'Name (Texto)')
        self.assertEqual(str(self.col2), 'Age (Entero)')

    def test_template_columns_ordering(self):
        cols = list(self.template.columns.values_list('name', flat=True))
        self.assertEqual(cols, ['Name', 'Age'])

    def test_template_unique_constraint(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            TableTemplate.objects.create(name='Test Template', owner=self.user)

    def test_cascade_delete_user(self):
        user_pk = self.user.pk
        self.user.delete()
        self.assertEqual(TableTemplate.objects.filter(owner_id=user_pk).count(), 0)

    def test_cascade_delete_template(self):
        tpl_pk = self.template.pk
        self.template.delete()
        self.assertEqual(TemplateColumn.objects.filter(template_id=tpl_pk).count(), 0)


# ──────────────────────────────────────────────
#  Dataset Model Tests
# ──────────────────────────────────────────────

class DatasetModelTests(TestCase):
    """Tests for the Dataset model."""

    def setUp(self):
        self.user = User.objects.create_user(username='dstest', password='testpass123')
        self.template = TableTemplate.objects.create(
            name='Sales Template', owner=self.user,
        )
        TemplateColumn.objects.create(template=self.template, name='Item', data_type='text', order=0)
        TemplateColumn.objects.create(template=self.template, name='Amount', data_type='float', order=1)

        self.dataset = Dataset.objects.create(
            name='Q1 Sales', owner=self.user, template=self.template,
        )

    def test_dataset_creation(self):
        self.assertEqual(str(self.dataset), 'Q1 Sales')
        self.assertEqual(self.dataset.status, 'empty')
        self.assertEqual(self.dataset.row_count, 0)

    def test_dataset_default_status(self):
        self.assertEqual(self.dataset.status, 'empty')

    def test_dataset_unique_constraint(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Dataset.objects.create(
                name='Q1 Sales', owner=self.user, template=self.template,
            )

    def test_dataset_different_template_same_name(self):
        """Same name is OK if template is different."""
        other_tpl = TableTemplate.objects.create(name='Other Template', owner=self.user)
        ds = Dataset.objects.create(
            name='Q1 Sales', owner=self.user, template=other_tpl,
        )
        self.assertIsNotNone(ds.pk)

    def test_cascade_delete_user(self):
        user_pk = self.user.pk
        self.user.delete()
        self.assertEqual(Dataset.objects.filter(owner_id=user_pk).count(), 0)

    def test_cascade_delete_template(self):
        tpl_pk = self.template.pk
        self.template.delete()
        self.assertEqual(Dataset.objects.filter(template_id=tpl_pk).count(), 0)

    def test_status_choices(self):
        for status_val, _ in Dataset.STATUS_CHOICES:
            self.dataset.status = status_val
            self.dataset.save()
            self.dataset.refresh_from_db()
            self.assertEqual(self.dataset.status, status_val)


class DatasetImportModelTests(TestCase):
    """Tests for the DatasetImport model."""

    def setUp(self):
        self.user = User.objects.create_user(username='imptest', password='testpass123')
        self.template = TableTemplate.objects.create(name='Imp Template', owner=self.user)
        self.dataset = Dataset.objects.create(
            name='Imp Dataset', owner=self.user, template=self.template,
        )

    def test_import_creation(self):
        imp = DatasetImport.objects.create(
            dataset=self.dataset,
            source_filename='test.csv',
            mode='replace',
            status='pending',
        )
        self.assertIn('test.csv', str(imp))
        self.assertEqual(imp.total_rows, 0)
        self.assertEqual(imp.extra_columns_json, [])
        self.assertEqual(imp.missing_columns_json, [])
        self.assertEqual(imp.header_mapping_json, {})

    def test_cascade_delete_dataset(self):
        DatasetImport.objects.create(
            dataset=self.dataset, source_filename='a.csv', mode='replace',
        )
        ds_pk = self.dataset.pk
        self.dataset.delete()
        self.assertEqual(DatasetImport.objects.filter(dataset_id=ds_pk).count(), 0)


class DatasetRowModelTests(TestCase):
    """Tests for the DatasetRow model."""

    def setUp(self):
        self.user = User.objects.create_user(username='rowtest', password='testpass123')
        self.template = TableTemplate.objects.create(name='Row Template', owner=self.user)
        self.dataset = Dataset.objects.create(
            name='Row Dataset', owner=self.user, template=self.template,
        )
        self.imp = DatasetImport.objects.create(
            dataset=self.dataset, source_filename='rows.csv', mode='replace',
        )

    def test_row_creation(self):
        row = DatasetRow.objects.create(
            dataset=self.dataset,
            dataset_import=self.imp,
            row_index=1,
            data_json={'1': 'Hello', '2': '42'},
        )
        self.assertEqual(str(row), 'Row 1 (Dataset: Row Dataset)')
        self.assertTrue(row.is_valid)
        self.assertEqual(row.issue_count, 0)

    def test_row_ordering(self):
        for i in [3, 1, 2]:
            DatasetRow.objects.create(
                dataset=self.dataset, dataset_import=self.imp,
                row_index=i, data_json={},
            )
        indices = list(DatasetRow.objects.filter(
            dataset=self.dataset
        ).values_list('row_index', flat=True))
        self.assertEqual(indices, [1, 2, 3])

    def test_cascade_delete_import(self):
        DatasetRow.objects.create(
            dataset=self.dataset, dataset_import=self.imp,
            row_index=1, data_json={},
        )
        imp_pk = self.imp.pk
        self.imp.delete()
        self.assertEqual(DatasetRow.objects.filter(dataset_import_id=imp_pk).count(), 0)


class DatasetCellIssueModelTests(TestCase):
    """Tests for the DatasetCellIssue model."""

    def setUp(self):
        self.user = User.objects.create_user(username='issuetest', password='testpass123')
        self.template = TableTemplate.objects.create(name='Issue Template', owner=self.user)
        self.col = TemplateColumn.objects.create(
            template=self.template, name='Email', data_type='email', order=0,
        )
        self.dataset = Dataset.objects.create(
            name='Issue Dataset', owner=self.user, template=self.template,
        )
        self.imp = DatasetImport.objects.create(
            dataset=self.dataset, source_filename='issues.csv', mode='replace',
        )
        self.row = DatasetRow.objects.create(
            dataset=self.dataset, dataset_import=self.imp,
            row_index=1, data_json={}, is_valid=False, issue_count=1,
        )

    def test_issue_creation(self):
        issue = DatasetCellIssue.objects.create(
            dataset_row=self.row,
            template_column=self.col,
            raw_value='not-an-email',
            issue_code='invalid_email',
            message='"not-an-email" no es un correo electrónico válido',
        )
        self.assertIn('Email', str(issue))
        self.assertIn('invalid_email', str(issue.issue_code))

    def test_issue_column_set_null(self):
        """When a column is deleted, the issue's FK is set to null (not deleted)."""
        issue = DatasetCellIssue.objects.create(
            dataset_row=self.row,
            template_column=self.col,
            raw_value='bad',
            issue_code='invalid_email',
            message='test',
        )
        self.col.delete()
        issue.refresh_from_db()
        self.assertIsNone(issue.template_column)

    def test_cascade_delete_row(self):
        DatasetCellIssue.objects.create(
            dataset_row=self.row, template_column=self.col,
            raw_value='x', issue_code='invalid_email', message='test',
        )
        row_pk = self.row.pk
        self.row.delete()
        self.assertEqual(DatasetCellIssue.objects.filter(dataset_row_id=row_pk).count(), 0)
