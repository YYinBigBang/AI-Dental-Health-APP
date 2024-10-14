
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import transaction
from django.contrib.auth import get_user_model, authenticate

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


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                tokens = get_tokens_for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            tokens = get_tokens_for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)


class SchoolViewSet(viewsets.ModelViewSet):
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


class TeacherProfileViewSet(viewsets.ModelViewSet):
    """Teacher CRUD: Teachers can only manage their classrooms."""
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated, IsTeacher, IsOwner]

    def get_queryset(self):
        teacher_profile = getattr(self.request.user, 'teacherprofile', None)
        if teacher_profile:
            return TeacherProfile.objects.filter(pk=teacher_profile.pk)
        return TeacherProfile.objects.none()


class ClassroomViewSet(viewsets.ModelViewSet):
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


class StudentProfileViewSet(viewsets.ModelViewSet):
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


class ParentViewSet(viewsets.ModelViewSet):
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


class ParentStudentRelationshipViewSet(viewsets.ModelViewSet):
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

