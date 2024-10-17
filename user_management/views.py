
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.http import Http404
from django.db import transaction
from django.contrib.auth import get_user_model, authenticate
from dental_health_service.django_utils import standard_response

from .models import (
    School,
    TeacherProfile,
    Classroom,
    StudentProfile,
    Parent,
    ParentStudentRelationship
)
from .permissions import (
    IsSuperuser,
    IsTeacher,
    IsStudent,
    IsParent,
    CanManageClassroom,
    CanManageStudents,
    CanManageParents,
    CanManageParentStudentRelationship,
    IsOwner
)
from .serializers import (
    UserSerializer,
    SchoolSerializer,
    TeacherProfileSerializer,
    ClassroomSerializer,
    StudentProfileSerializer,
    ParentSerializer,
    ParentStudentRelationshipSerializer
)

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class CustomPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return standard_response(
            returncode=0,
            message="資料獲取成功",
            data={
                "results": data,
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
            status_code=status.HTTP_200_OK
        )


class CustomModelViewSet(viewsets.ModelViewSet):
    """Custom ModelViewSet that uses standard_response for CRUD operations."""
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return standard_response(
            returncode=0,
            message="資料獲取成功",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return standard_response(
                returncode=1,
                message="資料未找到!!",
                data=True,
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(instance)
        return standard_response(
            returncode=0,
            message="資料獲取成功",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return standard_response(
            returncode=0,
            message="資料創建成功",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return standard_response(
            returncode=0,
            message="資料更新成功",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return standard_response(
            returncode=0,
            message="資料刪除成功!!",
            data=True,
            status_code=status.HTTP_204_NO_CONTENT
        )


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                tokens = get_tokens_for_user(user)
            return standard_response(
                message="User created successfully",
                data={
                    'user': UserSerializer(user).data,
                    'tokens': tokens
                }, status_code=status.HTTP_201_CREATED
            )
        return standard_response(
            returncode=1,
            message="註冊失敗！！",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            tokens = get_tokens_for_user(user)
            return standard_response(
                message="Login successful",
                data={
                    'user': UserSerializer(user).data,
                    'tokens': tokens
                }, status_code=status.HTTP_200_OK
            )
        return standard_response(returncode=1, message="無效憑證", status_code=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return standard_response(
                returncode=1,
                message="需要刷新憑證",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return standard_response(message="成功登出", status_code=status.HTTP_204_NO_CONTENT)
        except Exception:
            return standard_response(returncode=1, message="無效刷新憑證", status_code=status.HTTP_400_BAD_REQUEST)


class SchoolViewSet(CustomModelViewSet):
    """School CRUD - Only Superusers can manage schools."""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsSuperuser]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsSuperuser]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]


class TeacherProfileViewSet(CustomModelViewSet):
    """Teacher CRUD: Teachers can only manage their classrooms."""
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated, IsTeacher, IsOwner]

    def get_queryset(self):
        teacher_profile = getattr(self.request.user, 'teacherprofile', None)
        if teacher_profile:
            return TeacherProfile.objects.filter(pk=teacher_profile.pk)
        return TeacherProfile.objects.none()


class ClassroomViewSet(CustomModelViewSet):
    """Classroom CRUD: Teachers can manage classrooms they are assigned to."""
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [IsAuthenticated, IsTeacher, CanManageClassroom]

    def get_queryset(self):
        teacher = self.request.user.teacherprofile
        return Classroom.objects.filter(teachers=teacher)

    def perform_create(self, serializer):
        # Ensure that the classroom is linked to the teacher creating it
        teacher = self.request.user.teacherprofile
        classroom = serializer.save()
        classroom.teachers.add(teacher)


class StudentProfileViewSet(CustomModelViewSet):
    """
    Student CRUD:
    Teachers can manage students in their classroom.
    Students can only update their own profiles.
    """
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            # Students can only access and update their own profiles
            if hasattr(self.request.user, 'studentprofile'):
                return [IsStudent(), IsOwner()]
            # Teachers can manage students in their classroom
            elif hasattr(self.request.user, 'teacherprofile'):
                return [IsTeacher(), CanManageStudents()]

        # Only teachers can perform these actions
        elif self.action in ['create', 'list', 'destroy']:
            if hasattr(self.request.user, 'teacherprofile'):
                return [IsTeacher(), CanManageStudents()]

        # Fallback to default permission handling
        return super().get_permissions()

    def get_queryset(self):
        if hasattr(self.request.user, 'teacherprofile'):
            teacher = self.request.user.teacherprofile
            return StudentProfile.objects.filter(classroom__teachers=teacher)
        elif hasattr(self.request.user, 'studentprofile'):
            student = self.request.user.studentprofile
            return StudentProfile.objects.filter(pk=student.pk)
        else:
            return StudentProfile.objects.none()


class ParentViewSet(CustomModelViewSet):
    """
    Parent CRUD:
    Teachers can manage parents of students in their classroom.
    Parents can view and update their own profiles.
    Students can view their parents.
    """
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if hasattr(self.request.user, 'teacherprofile'):
            # Teachers can manage
            return [IsTeacher(), CanManageParents()]
        elif hasattr(self.request.user, 'parent'):
            # Parents can view and update their own data
            if self.action in ['retrieve', 'update', 'partial_update']:
                return [IsParent(), IsOwner()]
            else:
                return [IsParent()]
        elif hasattr(self.request.user, 'studentprofile'):
            # Students can only view
            if self.action in ['list', 'retrieve']:
                return [IsStudent()]
            else:
                return [IsAuthenticated()]
        else:
            return [IsAuthenticated()]

    def get_queryset(self):
        if hasattr(self.request.user, 'teacherprofile'):
            teacher = self.request.user.teacherprofile
            # Get parents of students in the teacher's classroom
            student_ids = StudentProfile.objects.filter(
                classroom__teachers=teacher
            ).values_list('id', flat=True)
            parent_ids = ParentStudentRelationship.objects.filter(
                student_id__in=student_ids
            ).values_list('parent_id', flat=True)
            return Parent.objects.filter(id__in=parent_ids)
        elif hasattr(self.request.user, 'parent'):
            # Parent can view their own profile
            parent = self.request.user.parent
            return Parent.objects.filter(pk=parent.pk)
        elif hasattr(self.request.user, 'studentprofile'):
            # Students can view their parents
            student = self.request.user.studentprofile
            parent_ids = ParentStudentRelationship.objects.filter(
                student=student
            ).values_list('parent_id', flat=True)
            return Parent.objects.filter(id__in=parent_ids)
        else:
            return Parent.objects.none()


class ParentStudentRelationshipViewSet(CustomModelViewSet):
    """
    Parent-Student Relationship CRUD:
    Teachers can manage relationships for students in their classroom.
    Parents and students can view their relationships.
    """
    queryset = ParentStudentRelationship.objects.all()
    serializer_class = ParentStudentRelationshipSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if hasattr(self.request.user, 'teacherprofile'):
            # Teachers can manage
            return [IsTeacher(), CanManageParentStudentRelationship()]
        elif hasattr(self.request.user, 'parent'):
            # Parents can view and update their own data
            if self.action in ['retrieve', 'update', 'partial_update']:
                return [IsParent(), IsOwner()]
            else:
                return [IsParent()]
        elif hasattr(self.request.user, 'studentprofile'):
            # Students can only view
            if self.action in ['list', 'retrieve']:
                return [IsStudent()]
            else:
                return [IsAuthenticated()]
        else:
            return [IsAuthenticated()]

    def get_queryset(self):
        if hasattr(self.request.user, 'teacherprofile'):
            teacher = self.request.user.teacherprofile
            # Get relationships for students in the teacher's classroom
            student_ids = StudentProfile.objects.filter(
                classroom__teachers=teacher
            ).values_list('id', flat=True)
            return ParentStudentRelationship.objects.filter(student_id__in=student_ids)
        elif hasattr(self.request.user, 'parent'):
            parent = self.request.user.parent
            return ParentStudentRelationship.objects.filter(parent=parent)
        elif hasattr(self.request.user, 'studentprofile'):
            student = self.request.user.studentprofile
            return ParentStudentRelationship.objects.filter(student=student)
        else:
            return ParentStudentRelationship.objects.none()

