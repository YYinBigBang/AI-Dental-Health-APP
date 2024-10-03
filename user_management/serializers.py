from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    TeacherProfile, StudentProfile, Parent, ParentStudentRelationship, School, Classroom
)
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TeacherSignupSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all())

    class Meta:
        model = TeacherProfile
        fields = ['id', 'user', 'school', 'gender', 'birth', 'phone_number']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        teacher_profile = TeacherProfile.objects.create(user=user, **validated_data)
        return teacher_profile


class StudentSignupSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.all())

    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'student_number', 'classroom', 'birth', 'gender']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        student_profile = StudentProfile.objects.create(user=user, **validated_data)
        return student_profile


class ParentSignupSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Parent
        fields = ['id', 'user', 'parent_name', 'phone_number']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        parent = Parent.objects.create(user=user, **validated_data)
        return parent


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = '__all__'


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'


class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = '__all__'


class ParentStudentRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentStudentRelationship
        fields = '__all__'

