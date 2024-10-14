from rest_framework import serializers
from .models import (
    User,
    School,
    TeacherProfile,
    Classroom,
    ClassroomTeacher,
    StudentProfile,
    Parent,
    ParentStudentRelationship
)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'full_name', 'email', 'line_id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'school_code', 'school_name', 'school_address']


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

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


class ClassroomSerializer(serializers.ModelSerializer):
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all())
    teachers = serializers.PrimaryKeyRelatedField(queryset=TeacherProfile.objects.all(), many=True)

    class Meta:
        model = Classroom
        fields = ['id', 'school', 'grade', 'class_name', 'teachers']

    def create(self, validated_data):
        teachers_data = validated_data.pop('teachers', [])
        classroom = Classroom.objects.create(**validated_data)
        classroom.teachers.set(teachers_data)
        return classroom

    def update(self, instance, validated_data):
        teachers_data = validated_data.pop('teachers', [])
        instance.grade = validated_data.get('grade', instance.grade)
        instance.class_name = validated_data.get('class_name', instance.class_name)
        instance.school = validated_data.get('school', instance.school)
        instance.save()
        if teachers_data:
            instance.teachers.set(teachers_data)
        return instance


class ClassroomTeacherSerializer(serializers.ModelSerializer):
    classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.all())  # Referenced by primary key
    teacher = serializers.PrimaryKeyRelatedField(queryset=TeacherProfile.objects.all())  # Referenced by primary key

    class Meta:
        model = ClassroomTeacher
        fields = ['id', 'classroom', 'teacher']

    def create(self, validated_data):
        return ClassroomTeacher.objects.create(**validated_data)


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'student_id', 'school', 'classroom', 'birth', 'gender']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        student_profile = StudentProfile.objects.create(user=user, **validated_data)
        return student_profile


class ParentSerializer(serializers.ModelSerializer):
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

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        instance.parent_name = validated_data.get('parent_name', instance.parent_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        return instance


class ParentStudentRelationshipSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(queryset=Parent.objects.all())
    student = serializers.PrimaryKeyRelatedField(queryset=StudentProfile.objects.all())

    class Meta:
        model = ParentStudentRelationship
        fields = ['id', 'parent', 'student', 'relationship']

