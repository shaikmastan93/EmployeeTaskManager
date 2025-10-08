from rest_framework import routers
from django.urls import path, include
from .views import EmployeeViewSet, TaskViewSet,UserRegisterView

router = routers.DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegisterView.as_view(), name='user-register'),
]

