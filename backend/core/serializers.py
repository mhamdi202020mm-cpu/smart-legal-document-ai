from rest_framework import serializers
from .models import Document,Client,Case
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse

User = get_user_model()


# تسجيل حساب جديد
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'phone']

    def validate_email(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError('الإيميل مطلوب!')
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('الإيميل ده مسجل قبل كده!')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'كلمتا السر غير متطابقتين!'})
        # قوة الباسورد (حسب AUTH_PASSWORD_VALIDATORS في settings)
        candidate = User(username=attrs.get('username', ''), email=attrs.get('email', ''))
        try:
            validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


# الملف الشخصي (عرض + تعديل)
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']   # ← دي للعرض بس


# تغيير كلمة السر — مش مربوط بجدول، فـ Serializer عادي مش ModelSerializer
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('كلمة السر القديمة غلط!')
        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value




class DocumentSerializer(serializers.ModelSerializer):
    # حقل إضافي مش موجود في الموديل: رابط كامل للملف
    file_url = serializers.SerializerMethodField()

    class Meta:
        read_only_fields = ['uploaded_by']   # ← الجديد: المستخدم ميقدرش يزوّر الرافع
        
        model = Document
        fields = ['id', 'title', 'file', 'file_url', 'status', 'case', 'uploaded_by', 'uploaded_at']
        extra_kwargs = {'file': {'write_only': True}}

    def validate_case(self, case):
        # المستند ممكن ما يبقاش تبع قضية — ساعتها مفيش حاجة نتحقق منها
        if case is None:
            return case
        # القضية لازم تكون تبع عميل من عملاء اليوزر الحالي
        if case.client.owner != self.context['request'].user:
            raise serializers.ValidationError('القضية دي مش بتاعتك!')
        return case

        # ← الجديد: التحقق من الملف قبل الحفظ
    def validate_file(self, file):
        if not file.name.lower().endswith('.pdf'):
            raise serializers.ValidationError('مسموح بملفات PDF فقط!')
        if file.size > 10 * 1024 * 1024:  # 10 ميجا
            raise serializers.ValidationError('حجم الملف أكبر من 10 ميجابايت!')
        # أي PDF حقيقي بيبدأ بـ %PDF- — مش كفاية نصدّق الامتداد
        header = file.read(5)
        file.seek(0)   # نرجّع المؤشر لأول الملف عشان يتحفظ كامل
        if header != b'%PDF-':
            raise serializers.ValidationError('الملف ده مش PDF حقيقي!')
        return file

    def get_file_url(self, obj):
        # رابط التنزيل المحمي: http://127.0.0.1:8000/api/documents/5/download/
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('document-download', args=[obj.pk]))

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
        # owner بيتحط من التوكن في perform_create، مش من اللي اليوزر يبعته
        read_only_fields = ['owner']


class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = '__all__'

    def validate_client(self, client):
        # القضية لازم تتربط بعميل بتاع اليوزر الحالي بس
        if client.owner != self.context['request'].user:
            raise serializers.ValidationError('العميل ده مش بتاعك!')
        return client