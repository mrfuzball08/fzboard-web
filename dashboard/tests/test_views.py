"""
View tests for the FuzBoard application.

Tests cover all view functions: authentication (login, register, logout),
dashboard access, template CRUD operations, and CSV download.
"""

import time

from django.test import TestCase, Client
from django.urls import reverse

from dashboard.models import User, TableTemplate, TemplateColumn


class AuthViewTests(TestCase):
    """Tests for authentication views: login, register, logout."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='authuser', email='auth@fzboard.test', password='testpass123',
        )

    # ── Login ─────────────────────────────────────────

    def test_login_page_loads(self):
        """GET /login/ renders the login page."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """POST /login/ with valid credentials redirects to dashboard."""
        response = self.client.post(reverse('login'), {
            'username': 'authuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid_credentials(self):
        """POST /login/ with wrong password stays on login page."""
        response = self.client.post(reverse('login'), {
            'username': 'authuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)

    def test_login_redirect_when_authenticated(self):
        """GET /login/ while logged in redirects to dashboard."""
        self.client.login(username='authuser', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)

    # ── Register ──────────────────────────────────────

    def test_register_page_loads(self):
        """GET /register/ renders the registration page."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_success(self):
        """POST /register/ with valid data creates user and redirects."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@fzboard.test',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_password_mismatch(self):
        """POST /register/ with mismatched passwords stays on register page."""
        response = self.client.post(reverse('register'), {
            'username': 'baduser',
            'email': 'bad@fzboard.test',
            'password1': 'Pass123!',
            'password2': 'DifferentPass!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_register_redirect_when_authenticated(self):
        """GET /register/ while logged in redirects to dashboard."""
        self.client.login(username='authuser', password='testpass123')
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)

    # ── Logout ────────────────────────────────────────

    def test_logout(self):
        """Logout redirects to login page."""
        self.client.login(username='authuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))


class DashboardViewTests(TestCase):
    """Tests for the dashboard view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dashuser', password='testpass123',
        )

    def test_dashboard_requires_login(self):
        """GET / without login redirects to /login/."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_dashboard_authenticated(self):
        """GET / while authenticated returns 200."""
        self.client.login(username='dashuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)


class TemplateListViewTests(TestCase):
    """Tests for the template list view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', email='test@fzboard.test', password='testpass123',
        )
        for i in range(5):
            tpl = TableTemplate.objects.create(
                name=f'Template {i+1}',
                description=f'Description for template {i+1}',
                owner=self.user,
            )
            for j in range(3):
                TemplateColumn.objects.create(
                    template=tpl, name=f'Column {j+1}', data_type='text', order=j,
                )

    def test_template_list_requires_login(self):
        response = self.client.get(reverse('template_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_template_list_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('template_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Template 1')
        self.assertContains(response, 'Template 5')

    def test_template_list_only_own_templates(self):
        other = User.objects.create_user(username='otheruser', password='testpass123')
        TableTemplate.objects.create(name='Other Template', owner=other)
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('template_list'))
        self.assertNotContains(response, 'Other Template')

    def test_template_list_search(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('template_list'), {'q': 'Template 3'})
        self.assertContains(response, 'Template 3')
        self.assertNotContains(response, 'Template 1')

    def test_template_count(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('template_list'))
        self.assertEqual(response.context['templates'].count(), 5)

    def test_template_list_response_time(self):
        self.client.login(username='testuser', password='testpass123')
        start = time.perf_counter()
        response = self.client.get(reverse('template_list'))
        elapsed = time.perf_counter() - start
        print(f"\n  [PERF] Template list view: {elapsed:.4f}s (status {response.status_code})")
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 2.0)


class TemplateCreateViewTests(TestCase):
    """Tests for creating templates via the Svelte form's POST format.

    The Svelte TemplateForm component submits data using Django's
    modelformset_factory format with prefix='form'.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='createuser', password='testpass123',
        )
        self.client.login(username='createuser', password='testpass123')

    def _post_data(self, name='My Template', description='Test description',
                   columns=None):
        """Build a dict matching the Svelte TemplateForm POST format."""
        if columns is None:
            columns = [
                {'name': 'Column 1', 'data_type': 'text'},
                {'name': 'Column 2', 'data_type': 'integer'},
            ]

        data = {
            'name': name,
            'description': description,
            'form-TOTAL_FORMS': str(len(columns)),
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
        }
        for i, col in enumerate(columns):
            data[f'form-{i}-name'] = col['name']
            data[f'form-{i}-data_type'] = col['data_type']
            data[f'form-{i}-order'] = str(i + 1)
        return data

    def test_create_page_loads(self):
        """GET /formatos/crear/ renders the create page."""
        response = self.client.get(reverse('template_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_requires_login(self):
        """POST /formatos/crear/ without login redirects."""
        self.client.logout()
        response = self.client.post(reverse('template_create'), self._post_data())
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_create_template_success(self):
        """POST with valid data creates template and columns, then redirects."""
        data = self._post_data(name='Created Template', columns=[
            {'name': 'Server', 'data_type': 'text'},
            {'name': 'IP', 'data_type': 'url'},
            {'name': 'Players', 'data_type': 'integer'},
        ])
        response = self.client.post(reverse('template_create'), data)
        self.assertEqual(response.status_code, 302)

        tpl = TableTemplate.objects.get(name='Created Template')
        self.assertEqual(tpl.owner, self.user)
        self.assertEqual(tpl.columns.count(), 3)
        col_names = list(tpl.columns.values_list('name', flat=True))
        self.assertEqual(col_names, ['Server', 'IP', 'Players'])

    def test_create_template_duplicate_name(self):
        """POST with a name that already exists shows error instead of 500."""
        TableTemplate.objects.create(name='Duplicate', owner=self.user)
        data = self._post_data(name='Duplicate')
        response = self.client.post(reverse('template_create'), data)
        # Should stay on the page (200), not crash (500)
        self.assertEqual(response.status_code, 200)
        # Should still only be one template with that name
        self.assertEqual(
            TableTemplate.objects.filter(name='Duplicate', owner=self.user).count(), 1
        )

    def test_create_template_empty_name(self):
        """POST with empty name stays on the form page."""
        data = self._post_data(name='')
        response = self.client.post(reverse('template_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TableTemplate.objects.count(), 0)

    def test_create_template_all_data_types(self):
        """POST with all 7 column data types succeeds."""
        columns = [
            {'name': 'Text Col', 'data_type': 'text'},
            {'name': 'Int Col', 'data_type': 'integer'},
            {'name': 'Float Col', 'data_type': 'float'},
            {'name': 'Date Col', 'data_type': 'date'},
            {'name': 'Bool Col', 'data_type': 'boolean'},
            {'name': 'Email Col', 'data_type': 'email'},
            {'name': 'URL Col', 'data_type': 'url'},
        ]
        data = self._post_data(name='All Types', columns=columns)
        response = self.client.post(reverse('template_create'), data)
        self.assertEqual(response.status_code, 302)

        tpl = TableTemplate.objects.get(name='All Types')
        self.assertEqual(tpl.columns.count(), 7)


class TemplateDetailViewTests(TestCase):
    """Tests for viewing and editing templates (inline formset via Svelte)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='detailuser', password='testpass123',
        )
        self.client.login(username='detailuser', password='testpass123')
        self.template = TableTemplate.objects.create(
            name='Detail Template', description='Testing detail', owner=self.user,
        )
        self.col1 = TemplateColumn.objects.create(
            template=self.template, name='Name', data_type='text', order=0,
        )
        self.col2 = TemplateColumn.objects.create(
            template=self.template, name='Email', data_type='email', order=1,
        )

    def _edit_data(self, name=None, description=None, columns=None):
        """Build POST data matching inlineformset_factory with prefix='form'."""
        name = name or self.template.name
        description = description if description is not None else self.template.description

        if columns is None:
            columns = [
                {'id': str(self.col1.pk), 'name': 'Name', 'data_type': 'text'},
                {'id': str(self.col2.pk), 'name': 'Email', 'data_type': 'email'},
            ]

        initial_count = sum(1 for c in columns if c.get('id'))
        data = {
            'name': name,
            'description': description,
            'form-TOTAL_FORMS': str(len(columns)),
            'form-INITIAL_FORMS': str(initial_count),
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
        }
        for i, col in enumerate(columns):
            data[f'form-{i}-name'] = col['name']
            data[f'form-{i}-data_type'] = col['data_type']
            data[f'form-{i}-order'] = str(i + 1)
            if col.get('id'):
                data[f'form-{i}-id'] = col['id']
            if col.get('DELETE'):
                data[f'form-{i}-DELETE'] = 'on'
        return data

    def test_detail_page_loads(self):
        """GET /formatos/<pk>/ renders the detail page."""
        response = self.client.get(reverse('template_detail', args=[self.template.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detail Template')

    def test_detail_requires_login(self):
        """Unauthenticated users are redirected from detail page."""
        self.client.logout()
        response = self.client.get(reverse('template_detail', args=[self.template.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_detail_other_user_template_returns_404(self):
        """Users cannot access other users' templates."""
        other = User.objects.create_user(username='otheruser', password='testpass123')
        other_tpl = TableTemplate.objects.create(name='Other', owner=other)
        response = self.client.get(reverse('template_detail', args=[other_tpl.pk]))
        self.assertEqual(response.status_code, 404)

    def test_edit_template_name(self):
        """POST with updated name saves correctly and redirects."""
        data = self._edit_data(name='Renamed Template')
        response = self.client.post(
            reverse('template_detail', args=[self.template.pk]), data
        )
        self.assertEqual(response.status_code, 302)
        self.template.refresh_from_db()
        self.assertEqual(self.template.name, 'Renamed Template')

    def test_edit_add_column(self):
        """POST with a new column (no id) adds it to the template."""
        columns = [
            {'id': str(self.col1.pk), 'name': 'Name', 'data_type': 'text'},
            {'id': str(self.col2.pk), 'name': 'Email', 'data_type': 'email'},
            {'name': 'Age', 'data_type': 'integer'},  # New column, no id
        ]
        data = self._edit_data(columns=columns)
        response = self.client.post(
            reverse('template_detail', args=[self.template.pk]), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.template.columns.count(), 3)

    def test_edit_delete_column(self):
        """POST with DELETE flag removes the column."""
        columns = [
            {'id': str(self.col1.pk), 'name': 'Name', 'data_type': 'text'},
            {'id': str(self.col2.pk), 'name': 'Email', 'data_type': 'email', 'DELETE': True},
        ]
        data = self._edit_data(columns=columns)
        response = self.client.post(
            reverse('template_detail', args=[self.template.pk]), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.template.columns.count(), 1)
        self.assertEqual(self.template.columns.first().name, 'Name')


class TemplateDeleteViewTests(TestCase):
    """Tests for deleting templates."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deluser', password='testpass123',
        )
        self.client.login(username='deluser', password='testpass123')
        self.template = TableTemplate.objects.create(
            name='To Delete', description='Delete me', owner=self.user,
        )

    def test_delete_confirmation_page(self):
        """GET /formatos/<pk>/eliminar/ shows confirmation page."""
        response = self.client.get(reverse('template_delete', args=[self.template.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'To Delete')

    def test_delete_template_success(self):
        """POST /formatos/<pk>/eliminar/ deletes and redirects to list."""
        response = self.client.post(reverse('template_delete', args=[self.template.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TableTemplate.objects.filter(pk=self.template.pk).exists())

    def test_delete_other_user_template_returns_404(self):
        """Users cannot delete other users' templates."""
        other = User.objects.create_user(username='otheruser', password='testpass123')
        other_tpl = TableTemplate.objects.create(name='Other', owner=other)
        response = self.client.post(reverse('template_delete', args=[other_tpl.pk]))
        self.assertEqual(response.status_code, 404)


class TemplateDownloadCSVTests(TestCase):
    """Tests for CSV download functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='csvuser', password='testpass123',
        )
        self.client.login(username='csvuser', password='testpass123')
        self.template = TableTemplate.objects.create(
            name='CSV Template', owner=self.user,
        )
        TemplateColumn.objects.create(
            template=self.template, name='Name', data_type='text', order=0,
        )
        TemplateColumn.objects.create(
            template=self.template, name='Age', data_type='integer', order=1,
        )

    def test_download_csv(self):
        """GET /formatos/<pk>/descargar/ returns a CSV file."""
        response = self.client.get(
            reverse('template_download_csv', args=[self.template.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('CSV Template.csv', response['Content-Disposition'])

    def test_csv_content(self):
        """CSV file contains correct headers and type hints."""
        response = self.client.get(
            reverse('template_download_csv', args=[self.template.pk])
        )
        # Decode and check content (skip BOM)
        content = response.content.decode('utf-8-sig')
        lines = content.strip().split('\r\n')
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'Name,Age')
        self.assertEqual(lines[1], 'Texto,Entero')

    def test_download_other_user_csv_returns_404(self):
        """Users cannot download other users' template CSVs."""
        other = User.objects.create_user(username='otheruser', password='testpass123')
        other_tpl = TableTemplate.objects.create(name='Other CSV', owner=other)
        response = self.client.get(
            reverse('template_download_csv', args=[other_tpl.pk])
        )
        self.assertEqual(response.status_code, 404)
