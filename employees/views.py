from rest_framework import viewsets,filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Employee, Task
from .serializers import EmployeeSerializer, TaskSerializer ,UserRegisterSerializer
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now, timedelta
import random
from .models import PasswordResetOTP, EmailVerificationToken, UserProfile
from .serializers import (
    UserRegisterSerializer,
    RequestPasswordResetSerializer,
    VerifyOTPResetSerializer,
    ChangePasswordSerializer,
)
from .utils import send_email


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class TaskViewSet(viewsets.ModelViewSet):
    # queryset = Task.objects.all()
    queryset = Task.objects.select_related('assigned_to').all()
    serializer_class = TaskSerializer

    # Add filtering and searching
    # Add powerful filtering, searching & ordering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # filterset_fields = ['status', 'assigned_to']  # Filter by status and employee
     # ✅ Filter by exact status and employee name
    filterset_fields = {
        'status': ['exact'],
        'assigned_to__name': ['exact', 'icontains'],
    }
    # search_fields = ['title', 'description']  # Optional: search by title or description
        # ✅ Search across multiple fields
    search_fields = ['title', 'description', 'assigned_to__name']

        # ✅ Allow ordering by date fields
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']  # Default ordering (latest first)


# --- Registration view already exists: UserRegisterView -- keep it -- after creating user we must create & send email verification

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save()
        # create email verification token
        expiry = timezone.now() + timedelta(days=1)
        token_obj = EmailVerificationToken.objects.create(user=user, expires_at=expiry)
        verify_link = self.request.build_absolute_uri(
            reverse('verify-email', kwargs={'token': str(token_obj.token)})
        )
        subject = "Verify your email"
        message = f"Hi {user.username},\n\nClick the link to verify your email:\n{verify_link}\n\nThis link expires in 24 hours."
        send_email(subject, message, [user.email])

# --- Email verification view ---
from rest_framework.views import APIView

class VerifyEmailView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, token):
        token_obj = get_object_or_404(EmailVerificationToken, token=token, used=False)
        if token_obj.expires_at < timezone.now():
            return Response({"detail": "Token expired."}, status=status.HTTP_400_BAD_REQUEST)
        # mark user active and profile email_verified True
        user = token_obj.user
        user.is_active = True
        user.save()
        # mark token used
        token_obj.used = True
        token_obj.save()
        # mark profile verified
        if hasattr(user, 'profile'):
            user.profile.email_verified = True
            user.profile.save()
        return Response({"detail": "Email verified successfully."}, status=status.HTTP_200_OK)

# --- Request password reset (generate OTP and email) ---
class RequestPasswordResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # For security, don't reveal whether email exists
            return Response({"detail": "If the email exists, an OTP has been sent."}, status=status.HTTP_200_OK)

        # generate 6-digit OTP
        otp_code = f"{random.randint(0, 999999):06d}"
        expiry = timezone.now() + timedelta(minutes=15)
        PasswordResetOTP.objects.create(user=user, otp=otp_code, expires_at=expiry)
        subject = "Your password reset OTP"
        message = f"Hi {user.username},\n\nYour OTP is: {otp_code}\nIt expires in 15 minutes."
        send_email(subject, message, [email])
        return Response({"detail": "If the email exists, an OTP has been sent."}, status=status.HTTP_200_OK)

# --- Verify OTP and reset password ---
class VerifyOTPAndResetView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = VerifyOTPResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        # find latest matching OTP not used
        try:
            otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp, used=False).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.expires_at < timezone.now():
            return Response({"detail": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        # set new password
        user.set_password(new_password)
        user.save()
        # mark OTP used
        otp_obj.used = True
        otp_obj.save()

        # update password_changed_at to now (this will invalidate old tokens via custom auth)
        if hasattr(user, 'profile'):
            user.profile.password_changed_at = timezone.now()
            user.profile.save()

        return Response({"detail": "Password reset successful."}, status=status.HTTP_200_OK)

# --- Change password (authenticated user) ---
from rest_framework.permissions import IsAuthenticated

class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        if not user.check_password(old_password):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        # update password_changed_at to now to logout from all devices
        if hasattr(user, 'profile'):
            user.profile.password_changed_at = timezone.now()
            user.profile.save()

        return Response({"detail": "Password changed successfully. You have been logged out from other devices."}, status=status.HTTP_200_OK)