import time

from django.test import TestCase

from dashboard.models import User, TableTemplate, TemplateColumn


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
