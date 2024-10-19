
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    SignupView,
    LoginView,
    LogoutView,
    SchoolViewSet,
    TeacherProfileViewSet,
    ClassroomViewSet,
    StudentProfileViewSet,
    ParentViewSet,
    ParentStudentRelationshipViewSet,
)

router = DefaultRouter()
router.register(r'schools', SchoolViewSet)
router.register(r'teachers', TeacherProfileViewSet)
router.register(r'classrooms', ClassroomViewSet)
router.register(r'students', StudentProfileViewSet)
router.register(r'parents', ParentViewSet)
router.register(r'parent-student-relationships', ParentStudentRelationshipViewSet)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include(router.urls)),
]