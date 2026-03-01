"""
Volume / stress tests for the FuzBoard application.

Tests how the system performs with different scales of data:
  - 50 users × 10 templates each
  - 50 users × 30 templates each
  - 100 users × 10 templates each
  - 100 users × 30 templates each

Each template gets 5 columns to simulate realistic data.
"""

import time

from django.test import TestCase, Client
from django.urls import reverse

from dashboard.models import User, TableTemplate, TemplateColumn


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _create_users(count: int):
    """Bulk-create `count` regular users and return them."""
    users = User.objects.bulk_create([
        User(username=f'user_{i}', email=f'user_{i}@fzboard.test')
        for i in range(count)
    ])
    # Set passwords (bulk_create doesn't hash them)
    for u in users:
        u.set_password('testpass123')
        u.save(update_fields=['password'])
    return users


def _create_templates_for_users(users, templates_per_user: int, columns_per_template: int = 5):
    """Create templates (with columns) for every user in the list."""
    templates = []
    for user in users:
        for t in range(templates_per_user):
            templates.append(TableTemplate(
                name=f'{user.username}_tpl_{t}',
                description=f'Template {t} for {user.username}',
                owner=user,
            ))
    TableTemplate.objects.bulk_create(templates)

    # Re-fetch to get PKs assigned by the DB
    all_templates = TableTemplate.objects.all()
    columns = []
    for tpl in all_templates:
        for c in range(columns_per_template):
            columns.append(TemplateColumn(
                template=tpl,
                name=f'col_{c}',
                data_type='text',
                order=c,
            ))
    TemplateColumn.objects.bulk_create(columns)


# ──────────────────────────────────────────────
#  Volume: 50 Users
# ──────────────────────────────────────────────

class Volume50Users10TemplatesTest(TestCase):
    """50 users × 10 templates each = 500 templates, 2 500 columns."""

    @classmethod
    def setUpTestData(cls):
        cls.users = _create_users(50)
        _create_templates_for_users(cls.users, templates_per_user=10)
        # Pick one user for authenticated view tests
        cls.test_user = cls.users[0]

    def test_user_count(self):
        self.assertEqual(User.objects.count(), 50)

    def test_template_count(self):
        self.assertEqual(TableTemplate.objects.count(), 500)

    def test_column_count(self):
        self.assertEqual(TemplateColumn.objects.count(), 2500)

    def test_list_all_users_time(self):
        start = time.perf_counter()
        users = list(User.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 50u×10t] All users query: {elapsed:.4f}s ({len(users)} users)")
        self.assertLess(elapsed, 1.0)

    def test_list_all_templates_time(self):
        start = time.perf_counter()
        templates = list(TableTemplate.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 50u×10t] All templates query: {elapsed:.4f}s ({len(templates)} templates)")
        self.assertLess(elapsed, 1.0)

    def test_list_user_templates_time(self):
        start = time.perf_counter()
        templates = list(TableTemplate.objects.filter(owner=self.test_user))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 50u×10t] User templates query: {elapsed:.4f}s ({len(templates)} templates)")
        self.assertEqual(len(templates), 10)
        self.assertLess(elapsed, 1.0)

    def test_template_list_view_time(self):
        client = Client()
        client.force_login(self.test_user)
        start = time.perf_counter()
        response = client.get(reverse('template_list'))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 50u×10t] Template list view: {elapsed:.4f}s (status {response.status_code})")
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 2.0)


class Volume50Users30TemplatesTest(TestCase):
    """50 users × 30 templates each = 1 500 templates, 7 500 columns."""

    @classmethod
    def setUpTestData(cls):
        cls.users = _create_users(50)
        _create_templates_for_users(cls.users, templates_per_user=30)
        cls.test_user = cls.users[0]

    def test_user_count(self):
        self.assertEqual(User.objects.count(), 50)

    def test_template_count(self):
        self.assertEqual(TableTemplate.objects.count(), 1500)

    def test_column_count(self):
        self.assertEqual(TemplateColumn.objects.count(), 7500)

    def test_list_all_users_time(self):
        start = time.perf_counter()
        users = list(User.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 50u×30t] All users query: {elapsed:.4f}s ({len(users)} users)")
        self.assertLess(elapsed, 1.0)

    def test_list_all_templates_time(self):
        start = time.perf_counter()
        templates = list(TableTemplate.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 50u×30t] All templates query: {elapsed:.4f}s ({len(templates)} templates)")
        self.assertLess(elapsed, 2.0)

    def test_list_user_templates_time(self):
        start = time.perf_counter()
        templates = list(TableTemplate.objects.filter(owner=self.test_user))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 50u×30t] User templates query: {elapsed:.4f}s ({len(templates)} templates)")
        self.assertEqual(len(templates), 30)
        self.assertLess(elapsed, 1.0)

    def test_template_list_view_time(self):
        client = Client()
        client.force_login(self.test_user)
        start = time.perf_counter()
        response = client.get(reverse('template_list'))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 50u×30t] Template list view: {elapsed:.4f}s (status {response.status_code})")
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 3.0)


# ──────────────────────────────────────────────
#  Volume: 100 Users
# ──────────────────────────────────────────────

class Volume100Users10TemplatesTest(TestCase):
    """100 users × 10 templates each = 1 000 templates, 5 000 columns."""

    @classmethod
    def setUpTestData(cls):
        cls.users = _create_users(100)
        _create_templates_for_users(cls.users, templates_per_user=10)
        cls.test_user = cls.users[0]

    def test_user_count(self):
        self.assertEqual(User.objects.count(), 100)

    def test_template_count(self):
        self.assertEqual(TableTemplate.objects.count(), 1000)

    def test_column_count(self):
        self.assertEqual(TemplateColumn.objects.count(), 5000)

    def test_list_all_users_time(self):
        start = time.perf_counter()
        users = list(User.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 100u×10t] All users query: {elapsed:.4f}s ({len(users)} users)")
        self.assertLess(elapsed, 1.0)

    def test_list_all_templates_time(self):
        start = time.perf_counter()
        templates = list(TableTemplate.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 100u×10t] All templates query: {elapsed:.4f}s ({len(templates)} templates)")
        self.assertLess(elapsed, 2.0)

    def test_list_user_templates_time(self):
        start = time.perf_counter()
        templates = list(TableTemplate.objects.filter(owner=self.test_user))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 100u×10t] User templates query: {elapsed:.4f}s ({len(templates)} templates)")
        self.assertEqual(len(templates), 10)
        self.assertLess(elapsed, 1.0)

    def test_template_list_view_time(self):
        client = Client()
        client.force_login(self.test_user)
        start = time.perf_counter()
        response = client.get(reverse('template_list'))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 100u×10t] Template list view: {elapsed:.4f}s (status {response.status_code})")
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 2.0)


class Volume100Users30TemplatesTest(TestCase):
    """100 users × 30 templates each = 3 000 templates, 15 000 columns."""

    @classmethod
    def setUpTestData(cls):
        cls.users = _create_users(100)
        _create_templates_for_users(cls.users, templates_per_user=30)
        cls.test_user = cls.users[0]

    def test_user_count(self):
        self.assertEqual(User.objects.count(), 100)

    def test_template_count(self):
        self.assertEqual(TableTemplate.objects.count(), 3000)

    def test_column_count(self):
        self.assertEqual(TemplateColumn.objects.count(), 15000)

    def test_list_all_users_time(self):
        start = time.perf_counter()
        users = list(User.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 100u×30t] All users query: {elapsed:.4f}s ({len(users)} users)")
        self.assertLess(elapsed, 1.0)

    def test_list_all_templates_time(self):
        start = time.perf_counter()
        templates = list(TableTemplate.objects.all())
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 100u×30t] All templates query: {elapsed:.4f}s ({len(templates)} templates)")
        self.assertLess(elapsed, 3.0)

    def test_list_user_templates_time(self):
        start = time.perf_counter()
        templates = list(TableTemplate.objects.filter(owner=self.test_user))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 100u×30t] User templates query: {elapsed:.4f}s ({len(templates)} templates)")
        self.assertEqual(len(templates), 30)
        self.assertLess(elapsed, 1.0)

    def test_template_list_view_time(self):
        client = Client()
        client.force_login(self.test_user)
        start = time.perf_counter()
        response = client.get(reverse('template_list'))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF 100u×30t] Template list view: {elapsed:.4f}s (status {response.status_code})")
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 3.0)
