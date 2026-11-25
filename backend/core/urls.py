from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentViewSet,
    ClientViewSet,
    CaseViewSet,
    RegisterView,
    ProfileView,
    ChangePasswordView,
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'cases', CaseViewSet, basename='case')

urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/profile/', ProfileView.as_view()),
    path('auth/change-password/', ChangePasswordView.as_view()),
] + router.urls