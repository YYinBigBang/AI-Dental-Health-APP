from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from . import views

urlpatterns = [
    # Authentication URLs
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # School CRUD
    path('schools/', views.school_list_create, name='school-list-create'),
    path('schools/<int:pk>/', views.school_detail, name='school-detail'),

    # TeacherProfile CRUD
    path('teachers/', views.teacher_list_create, name='teacher-list-create'),
    path('teachers/<int:pk>/', views.teacher_detail, name='teacher-detail'),

    # Classroom CRUD
    path('classrooms/', views.classroom_list_create, name='classroom-list-create'),
    path('classrooms/<int:pk>/', views.classroom_detail, name='classroom-detail'),

    # StudentProfile CRUD
    path('students/', views.student_list_create, name='student-list-create'),
    path('students/<int:pk>/', views.student_detail, name='student-detail'),

    # Parent CRUD
    path('parents/', views.parent_list_create, name='parent-list-create'),
    path('parents/<int:pk>/', views.parent_detail, name='parent-detail'),

    # ParentStudentRelationship CRUD
    path('relationships/', views.parent_student_relationship_list_create, name='relationship-list-create'),
    path('relationships/<int:pk>/', views.parent_student_relationship_detail, name='relationship-detail'),
]
