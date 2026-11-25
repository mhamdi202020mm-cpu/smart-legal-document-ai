from django.shortcuts import render
from django.http import FileResponse

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
from rest_framework_simplejwt.tokens import RefreshToken
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
