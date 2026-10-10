from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


# المستخدم المخصوص — عملناه دلوقتي عشان بعدين نقدر نضيف له أدوار ورقم هاتف
class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")

    def __str__(self):
        return self.username

class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name="الاسم")
    phone = models.CharField(max_length=20, blank=True, verbose_name="الهاتف")
    email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    

class Case(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'جارية'
        CLOSED = 'closed', 'مغلقة'

    title = models.CharField(max_length=255, verbose_name="عنوان القضية")
    # ← كل قضية تابعه لعميل واحد
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,      # مهم! اقرأ اللي تحت 👇
        related_name='cases',
        verbose_name="العميل",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Document(models.Model):
    # حالات المستند — جاهزين لمرحلة Celery بعدين
    class Status(models.TextChoices):
        PENDING = 'pending', 'في الانتظار'
        PROCESSING = 'processing', 'جاري المعالجة'
        COMPLETED = 'completed', 'مكتمل'
        FAILED = 'failed', 'فشل'

    title = models.CharField(max_length=255, verbose_name="اسم المستند")
    file = models.FileField(upload_to='documents/', verbose_name="الملف")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,      # ← مربوط بالمستخدم اللي رفعه
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="رفعه",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="الحالة",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    # اربط المستند بقضية (اختياري — ممكن مستند مش تابع لقضية)
    case = models.ForeignKey(
        Case,
        null=True,          # مسموح يكون فاضي في قاعدة البيانات
        blank=True,         # مسموح يكون فاضي في الفورم
        on_delete=models.SET_NULL,   # لو القضية اتمسحت، المستند يفضل موجود بس من غير قضية
        related_name='documents',
        verbose_name="القضية",
    )

    def __str__(self):
        return self.title



