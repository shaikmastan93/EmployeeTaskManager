from rest_framework import routers
from django.urls import path, include
from .views import EmployeeViewSet, TaskViewSet,UserRegisterView
from .views import (
    UserRegisterView, VerifyEmailView,
    RequestPasswordResetView, VerifyOTPAndResetView,
    ChangePasswordView
)


router = routers.DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('auth/request-reset/', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('auth/verify-otp-reset/', VerifyOTPAndResetView.as_view(), name='verify-otp-reset'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
]

