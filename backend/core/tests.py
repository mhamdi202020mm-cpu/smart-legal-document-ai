import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

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
        self.assertEqual(res.json()['count'], 0)

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
        self.assertEqual(res.json()['count'], 0)

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
        titles = [d['title'] for d in res.json()['results']]
        self.assertEqual(titles, ['في القضية'])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DocumentFileTests(APITestCase):
    """التحقق من الملف + حماية التنزيل + مسح الملف."""

    def setUp(self):
        self.ahmed = User.objects.create_user('ahmed_t', 'a@t.com', 'StrongPass#123')
        self.sara = User.objects.create_user('sara_t', 's@t.com', 'StrongPass#123')

    def upload(self, user, name='test.pdf', content=b'%PDF-1.4 test'):
        self.client.force_authenticate(user)
        f = SimpleUploadedFile(name, content, content_type='application/pdf')
        return self.client.post('/api/documents/', {'title': 'مستند', 'file': f}, format='multipart')

    def test_rejects_non_pdf_extension(self):
        res = self.upload(self.ahmed, name='virus.exe')
        self.assertEqual(res.status_code, 400)
        self.assertIn('file', res.json())

    def test_rejects_fake_pdf(self):
        res = self.upload(self.ahmed, content=b'MZ this is not a pdf')
        self.assertEqual(res.status_code, 400)
        self.assertIn('file', res.json())

    def test_rejects_too_big_file(self):
        big = b'%PDF-' + b'0' * (10 * 1024 * 1024)
        res = self.upload(self.ahmed, content=big)
        self.assertEqual(res.status_code, 400)

    def test_owner_can_download(self):
        doc_id = self.upload(self.ahmed).json()['id']
        res = self.client.get(f'/api/documents/{doc_id}/download/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b''.join(res.streaming_content), b'%PDF-1.4 test')

    def test_other_user_cannot_download(self):
        doc_id = self.upload(self.ahmed).json()['id']
        self.client.force_authenticate(self.sara)
        res = self.client.get(f'/api/documents/{doc_id}/download/')
        self.assertEqual(res.status_code, 404)

    def test_file_url_points_to_download(self):
        res = self.upload(self.ahmed)
        self.assertTrue(res.json()['file_url'].endswith(f"/api/documents/{res.json()['id']}/download/"))

    def test_delete_removes_file_from_disk(self):
        doc_id = self.upload(self.ahmed).json()['id']
        path = Document.objects.get(id=doc_id).file.path
        self.assertTrue(os.path.exists(path))
        self.client.delete(f'/api/documents/{doc_id}/')
        self.assertFalse(os.path.exists(path))


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('ahmed_t', 'a@t.com', 'StrongPass#123')

    def test_logout_blocks_refresh_token(self):
        refresh = str(RefreshToken.for_user(self.user))
        res = self.client.post('/api/auth/logout/', {'refresh': refresh})
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/api/auth/token/refresh/', {'refresh': refresh})
        self.assertEqual(res.status_code, 401)

    def test_change_password(self):
        self.client.force_authenticate(self.user)
        res = self.client.post('/api/auth/change-password/', {
            'old_password': 'StrongPass#123', 'new_password': 'EvenStronger#456',
        })
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('EvenStronger#456'))

    def test_change_password_wrong_old(self):
        self.client.force_authenticate(self.user)
        res = self.client.post('/api/auth/change-password/', {
            'old_password': 'wrong', 'new_password': 'EvenStronger#456',
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('old_password', res.json())

    def test_pagination_shape(self):
        self.client.force_authenticate(self.user)
        res = self.client.get('/api/documents/')
        self.assertEqual(set(res.json().keys()), {'count', 'next', 'previous', 'results'})


class RegisterTests(APITestCase):
    url = '/api/auth/register/'

    def data(self, **changes):
        # بيانات تسجيل سليمة — كل اختبار بيبوّظ حاجة واحدة بس
        d = {'username': 'newuser', 'email': 'new@t.com',
             'password': 'StrongPass#123', 'password2': 'StrongPass#123'}
        d.update(changes)
        return d

    def test_register_success_returns_tokens(self):
        res = self.client.post(self.url, self.data())
        self.assertEqual(res.status_code, 201)
        self.assertIn('access', res.json())
        self.assertIn('refresh', res.json())

    def test_duplicate_email_rejected(self):
        User.objects.create_user('old', 'new@t.com', 'StrongPass#123')
        res = self.client.post(self.url, self.data(email='NEW@t.com'))
        self.assertEqual(res.status_code, 400)
        self.assertIn('email', res.json())

    def test_password_mismatch_rejected(self):
        res = self.client.post(self.url, self.data(password2='Other#12345'))
        self.assertEqual(res.status_code, 400)
        self.assertIn('password2', res.json())

    def test_weak_password_rejected(self):
        res = self.client.post(self.url, self.data(password='12345678', password2='12345678'))
        self.assertEqual(res.status_code, 400)
        self.assertIn('password', res.json())
