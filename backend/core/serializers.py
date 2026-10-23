from rest_framework import serializers
from .models import Document,Client,Case
from django.contrib.auth import get_user_model

User = get_user_model()


# تسجيل حساب جديد
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'phone']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('كلمتا السر غير متطابقتين!')
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




class DocumentSerializer(serializers.ModelSerializer):
    # حقل إضافي مش موجود في الموديل: رابط كامل للملف
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title','file', 'file_url', 'status', 'uploaded_by', 'uploaded_at']
        extra_kwargs = {'file': {'write_only': True}}

        # ← الجديد: التحقق من الملف قبل الحفظ
    def validate_file(self, file):
        if not file.name.lower().endswith('.pdf'):
            raise serializers.ValidationError('مسموح بملفات PDF فقط!')
        if file.size > 10 * 1024 * 1024:  # 10 ميجا
            raise serializers.ValidationError('حجم الملف أكبر من 10 ميجابايت!')
        return file
    
    def get_file_url(self, obj):
        # بنبني الرابط الكامل: http://127.0.0.1:8000/media/documents/...
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = '__all__'