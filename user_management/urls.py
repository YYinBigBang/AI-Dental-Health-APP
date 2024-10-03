from django.urls import path
from .views import (
    TeacherSignupView,
    StudentSignupView,
    ParentSignupView,
    LoginView,
    TeacherProfileView,
    ClassroomView,
    StudentProfileView,
    ParentProfileView,
    ParentStudentView,
)

urlpatterns = [
    path('signup/teacher/', TeacherSignupView.as_view(), name='teacher_signup'),
    path('signup/student/', StudentSignupView.as_view(), name='student_signup'),
    path('signup/parent/', ParentSignupView.as_view(), name='parent_signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('teacher/profile/', TeacherProfileView.as_view(), name='teacher_profile'),
    path('teacher/classroom/<int:pk>/', ClassroomView.as_view(), name='teacher_classroom'),
    path('student/profile/', StudentProfileView.as_view(), name='student_profile'),
    path('parent/profile/', ParentProfileView.as_view(), name='parent_profile'),
    path('parent/students/', ParentStudentView.as_view(), name='parent_students'),
]