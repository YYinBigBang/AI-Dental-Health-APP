from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    TeacherProfile,
    StudentProfile,
    Parent,
    ParentStudentRelationship,
    School,
    Classroom
)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = TeacherProfile
        fields = ['id', 'user', 'school', 'gender', 'birth', 'phone_number']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer().create(user_data)
        teacher_profile = TeacherProfile.objects.create(user=user, **validated_data)
        return teacher_profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            UserSerializer().update(instance.user, user_data)

        instance.school = validated_data.get('school', instance.school)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.birth = validated_data.get('birth', instance.birth)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        return instance


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'student_number', 'classroom', 'birth', 'gender']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer().create(user_data)
        student_profile = StudentProfile.objects.create(user=user, **validated_data)
        return student_profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            UserSerializer().update(instance.user, user_data)

        instance.student_number = validated_data.get('student_number', instance.student_number)
        instance.classroom = validated_data.get('classroom', instance.classroom)
        instance.birth = validated_data.get('birth', instance.birth)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.save()
        return instance


class ParentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Parent
        fields = ['id', 'user', 'parent_name', 'phone_number']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer().create(user_data)
        parent = Parent.objects.create(user=user, **validated_data)
        return parent

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            UserSerializer().update(instance.user, user_data)

        instance.parent_name = validated_data.get('parent_name', instance.parent_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        return instance


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'


class ParentStudentRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentStudentRelationship
        fields = '__all__'

