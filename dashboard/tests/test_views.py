import time

from django.test import TestCase, Client
from django.urls import reverse

from dashboard.models import User, TableTemplate, TemplateColumn


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
