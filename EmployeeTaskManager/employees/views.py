from rest_framework import viewsets,filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Employee, Task
from .serializers import EmployeeSerializer, TaskSerializer ,UserRegisterSerializer
from rest_framework import generics
from django.contrib.auth.models import User

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


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = []  # Allow anyone to register