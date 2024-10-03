from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import TeacherProfile, Classroom, StudentProfile, Parent, ParentStudentRelationship
from .serializers import (
    TeacherSignupSerializer,
    StudentSignupSerializer,
    ParentSignupSerializer,
    UserSerializer,
    TeacherProfileSerializer,
    ClassroomSerializer,
    StudentProfileSerializer,
    ParentSerializer,
    ParentStudentRelationshipSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'user_id'


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class BaseSignupView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        user = profile.user
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class TeacherSignupView(BaseSignupView):
    serializer_class = TeacherSignupSerializer


class StudentSignupView(BaseSignupView):
    serializer_class = StudentSignupSerializer


class ParentSignupView(BaseSignupView):
    serializer_class = ParentSignupSerializer


class TeacherProfileView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeacherProfileSerializer

    def get_object(self):
        return self.request.user.teacherprofile


class ClassroomView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClassroomSerializer

    def get_queryset(self):
        return Classroom.objects.filter(teacher__user=self.request.user)


class StudentProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentProfileSerializer

    def get_object(self):
        return self.request.user.studentprofile


class ParentProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ParentSerializer

    def get_object(self):
        return self.request.user.parent


class ParentStudentView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ParentStudentRelationshipSerializer

    def get_queryset(self):
        return ParentStudentRelationship.objects.filter(parent__user=self.request.user)

