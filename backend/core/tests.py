from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Client, Case

User = get_user_model()


class OwnershipIsolationTests(APITestCase):
    """كل محامي يشوف عملاءه وقضاياه بس."""

    def setUp(self):
        self.ahmed = User.objects.create_user('ahmed_t', 'a@t.com', 'StrongPass#123')
        self.sara = User.objects.create_user('sara_t', 's@t.com', 'StrongPass#123')
        self.client_a = Client.objects.create(name='شركة النيل', owner=self.ahmed)
        self.case_a = Case.objects.create(title='قضية سرية', client=self.client_a)

    # ---------- العملاء ----------
    def test_user_sees_only_own_clients(self):
        self.client.force_authenticate(self.sara)
        res = self.client.get('/api/clients/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 0)

    def test_other_users_client_is_404(self):
        self.client.force_authenticate(self.sara)
        res = self.client.get(f'/api/clients/{self.client_a.id}/')
        self.assertEqual(res.status_code, 404)

    def test_cannot_delete_other_users_client(self):
        self.client.force_authenticate(self.sara)
        res = self.client.delete(f'/api/clients/{self.client_a.id}/')
        self.assertEqual(res.status_code, 404)
        self.assertTrue(Client.objects.filter(id=self.client_a.id).exists())

    def test_owner_is_taken_from_token_not_body(self):
        self.client.force_authenticate(self.sara)
        res = self.client.post('/api/clients/', {'name': 'عميل جديد', 'owner': self.ahmed.id})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Client.objects.get(id=res.json()['id']).owner, self.sara)

    # ---------- القضايا ----------
    def test_user_sees_only_own_cases(self):
        self.client.force_authenticate(self.sara)
        res = self.client.get('/api/cases/')
        self.assertEqual(len(res.json()), 0)

    def test_cannot_create_case_on_other_users_client(self):
        self.client.force_authenticate(self.sara)
        res = self.client.post('/api/cases/', {'title': 'حيلة', 'client': self.client_a.id})
        self.assertEqual(res.status_code, 400)
        self.assertIn('client', res.json())

    def test_can_create_case_on_own_client(self):
        self.client.force_authenticate(self.ahmed)
        res = self.client.post('/api/cases/', {'title': 'قضية جديدة', 'client': self.client_a.id})
        self.assertEqual(res.status_code, 201)
