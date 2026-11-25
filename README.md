# Smart Legal Document AI

نظام لإدارة المستندات القانونية للمحامين، مع مساعد ذكي بيجاوب من المستندات (قريبًا).

## المميزات الحالية

- تسجيل حساب، دخول، خروج، وتغيير كلمة السر (JWT)
- إدارة العملاء والقضايا والمستندات (PDF)
- كل محامي يشوف بياناته بس (عزل كامل بين المستخدمين)
- ملفات الـ PDF بتتنزل بعد التأكد من الصلاحية، مش من رابط مفتوح
- تقسيم القوايم لصفحات (20 عنصر في الصفحة)

## التشغيل

### المتطلبات

- Python 3.14
- Node.js 24
- Docker

### قاعدة البيانات

```powershell
docker compose up -d
```

بيشغّل Postgres (مع pgvector) على البورت `5433`، و Redis على `6379`.

### الباك اند

```powershell
cd backend
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
copy .env.example .env
```

افتح `backend/.env` واملا القيم. لعمل `SECRET_KEY` جديد:

```powershell
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(50))"
```

بعدين:

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

الـ API هيشتغل على `http://127.0.0.1:8000/api/`.

### الفرونت اند

```powershell
cd frontend
npm install
npm start
```

هيفتح على `http://localhost:3000`.

### الاختبارات

```powershell
cd backend
.\venv\Scripts\python.exe manage.py test core
```

## الـ API

| الرابط | الوظيفة |
|---|---|
| `POST /api/auth/register/` | حساب جديد (بيرجّع توكنات) |
| `POST /api/auth/token/` | تسجيل دخول |
| `POST /api/auth/token/refresh/` | تجديد الـ access token |
| `POST /api/auth/logout/` | تسجيل خروج (`{"refresh": "..."}`) |
| `POST /api/auth/change-password/` | تغيير كلمة السر |
| `GET/PATCH /api/auth/profile/` | الملف الشخصي |
| `/api/clients/` | العملاء |
| `/api/cases/` | القضايا (`?client=` ، `?status=`) |
| `/api/documents/` | المستندات (`?case=` ، `?status=` ، `?search=`) |
| `GET /api/documents/{id}/download/` | تنزيل ملف الـ PDF |

كل الروابط (ما عدا التسجيل والدخول) محتاجة `Authorization: Bearer <access token>`.
