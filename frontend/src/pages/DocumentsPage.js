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

  if (loading) return <p style={{ padding: '20px' }}>⏳ جاري التحميل...</p>;
  if (error) return <p style={{ padding: '20px', color: 'red' }}>{error}</p>;

  return (
    <div dir="rtl" style={{ padding: '20px' }}>
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
            <a href={doc.file_url} target="_blank" rel="noreferrer" style={{ marginRight: '10px' }}>
              📄 عرض الملف
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default DocumentsPage;
