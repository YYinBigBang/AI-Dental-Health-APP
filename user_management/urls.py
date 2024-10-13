
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
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
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include(router.urls)),
]