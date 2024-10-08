from django.contrib.auth.models import User
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    TeacherProfile,
    StudentProfile,
    Parent,
    ParentStudentRelationship,
    Classroom
)
from .serializers import (
    TeacherProfileSerializer,
    StudentProfileSerializer,
    ParentSerializer,
    ClassroomSerializer,
    ParentStudentRelationshipSerializer,
    UserSerializer
)


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class RegistrationViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    def create_profile(self, request, serializer_class):
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        user = profile.user
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='teacher')
    def register_teacher(self, request):
        return self.create_profile(request, TeacherProfileSerializer)

    @action(detail=False, methods=['post'], url_path='student')
    def register_student(self, request):
        return self.create_profile(request, StudentProfileSerializer)

    @action(detail=False, methods=['post'], url_path='parent')
    def register_parent(self, request):
        return self.create_profile(request, ParentSerializer)


class TeacherProfileViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeacherProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudentProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ParentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ParentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Parent.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClassroomViewSet(viewsets.ModelViewSet):
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, 'teacherprofile'):
            return Classroom.objects.filter(teacher=self.request.user.teacherprofile)
        return Classroom.objects.none()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.teacherprofile)


class ParentStudentRelationshipViewSet(viewsets.ModelViewSet):
    serializer_class = ParentStudentRelationshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, 'parent'):
            return ParentStudentRelationship.objects.filter(parent=self.request.user.parent)
        return ParentStudentRelationship.objects.none()

