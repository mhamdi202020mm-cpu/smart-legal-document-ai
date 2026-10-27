from django.shortcuts import render

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Document,Client,Case
from .serializers import DocumentSerializer,ClientSerializer, CaseSerializer

from rest_framework import generics, permissions
from .serializers import RegisterSerializer, ProfileSerializer
from django.contrib.auth import get_user_model 
User = get_user_model()
# أي حد يعمل حساب جديد
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]   # ← مفتوح للكل


# الملف الشخصي: المستخدم يشوف ويعدّل بياناته بس
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]   # ← لازم login!

    def get_object(self):
        return self.request.user   # ← "أنت ملك نفسك": بيرجع المستخدم الحالي من التوكن

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-uploaded_at')
    serializer_class = DocumentSerializer

        # ← الجديد: endpoint مخصوص للرفع على /api/documents/upload/
    @action(detail=False, methods=['post'])
    def upload(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    ## filters
    filterset_fields = ['case', 'status', 'uploaded_by']
    search_fields = ['title']
    ordering_fields = ['uploaded_at', 'title']

    def get_queryset(self):
        # كل مستخدم يشوف مستنداته بس!
            return Document.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        # الرافع هو المستخدم الحالي — من غير ما نسأل حد
        serializer.save(uploaded_by=self.request.user)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all().order_by('-created_at')
    serializer_class = ClientSerializer
    
    search_fields = ['name', 'email']



class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all().order_by('-created_at')
    serializer_class = CaseSerializer

    filterset_fields = ['client', 'status']
    search_fields = ['title']
