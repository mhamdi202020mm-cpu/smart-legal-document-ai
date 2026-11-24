import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Client, Case, Document

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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DocumentCaseLinkTests(APITestCase):
    """ربط المستند بالقضية: مسموح بقضاياك بس."""

    def setUp(self):
        self.ahmed = User.objects.create_user('ahmed_t', 'a@t.com', 'StrongPass#123')
        self.sara = User.objects.create_user('sara_t', 's@t.com', 'StrongPass#123')
        client_a = Client.objects.create(name='شركة النيل', owner=self.ahmed)
        self.case_a = Case.objects.create(title='قضية التعويض', client=client_a)

    def make_pdf(self):
        # ملف PDF وهمي صغير — كفاية للاختبار
        return SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')

    def test_upload_document_to_own_case(self):
        self.client.force_authenticate(self.ahmed)
        res = self.client.post('/api/documents/', {
            'title': 'العقد', 'file': self.make_pdf(), 'case': self.case_a.id,
        }, format='multipart')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['case'], self.case_a.id)

    def test_cannot_upload_document_to_other_users_case(self):
        self.client.force_authenticate(self.sara)
        res = self.client.post('/api/documents/', {
            'title': 'حيلة', 'file': self.make_pdf(), 'case': self.case_a.id,
        }, format='multipart')
        self.assertEqual(res.status_code, 400)
        self.assertIn('case', res.json())
        self.assertFalse(Document.objects.filter(uploaded_by=self.sara).exists())

    def test_upload_document_without_case(self):
        self.client.force_authenticate(self.ahmed)
        res = self.client.post('/api/documents/', {
            'title': 'مستند عام', 'file': self.make_pdf(),
        }, format='multipart')
        self.assertEqual(res.status_code, 201)
        self.assertIsNone(res.json()['case'])

    def test_filter_documents_by_case(self):
        self.client.force_authenticate(self.ahmed)
        self.client.post('/api/documents/', {
            'title': 'في القضية', 'file': self.make_pdf(), 'case': self.case_a.id,
        }, format='multipart')
        self.client.post('/api/documents/', {
            'title': 'برة القضية', 'file': self.make_pdf(),
        }, format='multipart')
        res = self.client.get(f'/api/documents/?case={self.case_a.id}')
        titles = [d['title'] for d in res.json()]
        self.assertEqual(titles, ['في القضية'])
