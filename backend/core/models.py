from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


# المستخدم المخصوص — عملناه دلوقتي عشان بعدين نقدر نضيف له أدوار ورقم هاتف
class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")

    def __str__(self):
        return self.username


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

    def __str__(self):
        return self.title
