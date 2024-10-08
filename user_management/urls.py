from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    RegistrationViewSet,
    TeacherProfileViewSet,
    StudentProfileViewSet,
    ParentProfileViewSet,
    ClassroomViewSet,
    ParentStudentRelationshipViewSet,
)

router = DefaultRouter()

router.register(r'signup', RegistrationViewSet, basename='signup')
router.register(r'teacher/profiles', TeacherProfileViewSet, basename='teacher-profiles')
router.register(r'student/profiles', StudentProfileViewSet, basename='student-profiles')
router.register(r'parent/profiles', ParentProfileViewSet, basename='parent-profiles')
router.register(r'classrooms', ClassroomViewSet, basename='classrooms')
router.register(r'parent-student-relationships', ParentStudentRelationshipViewSet, basename='parent-student-relationships')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]