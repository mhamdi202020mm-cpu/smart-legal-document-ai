from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    # حقل إضافي مش موجود في الموديل: رابط كامل للملف
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title', 'file_url', 'status', 'uploaded_by', 'uploaded_at']

    def get_file_url(self, obj):
        # بنبني الرابط الكامل: http://127.0.0.1:8000/media/documents/...
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None