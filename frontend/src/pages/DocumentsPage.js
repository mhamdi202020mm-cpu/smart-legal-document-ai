import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get('/documents/')
      .then((response) => {
        // results جوّه غلاف الـ Pagination
        setDocuments(response.data.results);
        setLoading(false);
      })
      .catch((err) => {
        if (err.response && err.response.status === 401) {
          // مفيش توكن أو انتهت صلاحيته -> رجّعه لصفحة الدخول
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          navigate('/login');
          return;
        }
        setError('حصل خطأ في جلب البيانات');
        setLoading(false);
      });
  }, [navigate]);

  // الملف محمي بالتوكن، فبنجيبه عن طريق api (اللي بيحط التوكن) بدل رابط <a> عادي
  const openFile = async (doc) => {
    try {
      const response = await api.get(`/documents/${doc.id}/download/`, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(response.data);
      window.open(url, '_blank');
    } catch (err) {
      setError('مش قادر أفتح الملف');
    }
  };

  // تسجيل الخروج: نلغي الـ refresh token على السيرفر، وفي كل الأحوال نمسح التوكنات
  const logout = async () => {
    const refresh = localStorage.getItem('refresh_token');
    try {
      await api.post('/auth/logout/', { refresh });
    } catch (err) {
      // حتى لو السيرفر رفض (توكن قديم مثلًا)، نكمّل الخروج
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/login');
    }
  };

  if (loading) return <p style={{ padding: '20px' }}>⏳ جاري التحميل...</p>;
  if (error) return <p style={{ padding: '20px', color: 'red' }}>{error}</p>;

  return (
    <div dir="rtl" style={{ padding: '20px' }}>
      <button onClick={logout} style={{ float: 'left' }}>🚪 تسجيل الخروج</button>
      <h1>📁 المستندات القانونية</h1>
      {documents.length === 0 && <p>مفيش مستندات لسه — ارفع أول واحد!</p>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {documents.map((doc) => (
          <li
            key={doc.id}
            style={{ padding: '12px', border: '1px solid #ddd', marginBottom: '8px', borderRadius: '6px' }}
          >
            <strong>{doc.title}</strong>
            <span style={{ marginRight: '10px', color: '#666' }}>({doc.status})</span>
            <button onClick={() => openFile(doc)} style={{ marginRight: '10px' }}>
              📄 عرض الملف
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default DocumentsPage;
