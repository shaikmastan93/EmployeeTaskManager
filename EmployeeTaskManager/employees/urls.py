from rest_framework import routers
from django.urls import path, include
from .views import EmployeeViewSet, TaskViewSet

router = routers.DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

