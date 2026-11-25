from django.contrib.auth import get_user_model
from django.http import FileResponse
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Document, Client, Case
from .serializers import (
    DocumentSerializer,
    ClientSerializer,
    CaseSerializer,
    RegisterSerializer,
    ProfileSerializer,
)

User = get_user_model()


# أي حد يعمل حساب جديد
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]   # ← مفتوح للكل

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)   # ← تسجيل دخول تلقائي بعد التسجيل
        return Response({
            'user': {'id': user.id, 'username': user.username, 'email': user.email},
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


# الملف الشخصي: المستخدم يشوف ويعدّل بياناته بس
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]   # ← لازم login!

    def get_object(self):
        return self.request.user   # ← "أنت ملك نفسك": بيرجع المستخدم الحالي من التوكن


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    filterset_fields = ['case', 'status']
    search_fields = ['title']
    ordering_fields = ['uploaded_at', 'title']

    def get_queryset(self):
        # كل مستخدم يشوف مستنداته بس!
        return Document.objects.filter(uploaded_by=self.request.user).order_by('-uploaded_at')

    def perform_create(self, serializer):
        # الرافع هو المستخدم الحالي — من غير ما نسأل حد
        serializer.save(uploaded_by=self.request.user)

    def perform_destroy(self, instance):
        # امسح المستند من الداتابيز الأول، وبعدين الملف من الهارد
        file = instance.file
        instance.delete()
        file.delete(save=False)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        # get_object بيدوّر جوه get_queryset ← مستند حد تاني = 404
        document = self.get_object()
        return FileResponse(
            document.file.open('rb'),
            content_type='application/pdf',
            filename=f'{document.title}.pdf',
        )

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    
    search_fields = ['name', 'email']

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)



class CaseViewSet(viewsets.ModelViewSet):
    serializer_class = CaseSerializer
    filterset_fields = ['client', 'status']
    search_fields = ['title']

    def get_queryset(self):
        return Case.objects.filter(client__owner=self.request.user).order_by('-created_at')
