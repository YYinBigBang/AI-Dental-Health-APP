
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# Choices for gender field
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.
    Additional common fields can be added here if necessary.
    """
    pass


class School(models.Model):
    """
    Represents a school.
    """
    name = models.CharField(max_length=255)
    verified_code = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class TeacherProfile(models.Model):
    """
    Stores additional information about a teacher, linked to a User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birth = models.DateField()
    phone_number = PhoneNumberField()

    def __str__(self):
        return self.user.get_full_name()


class Classroom(models.Model):
    """
    Represents a classroom, which can have multiple teachers and students.
    """
    grade = models.CharField(max_length=10)
    class_name = models.CharField(max_length=255)
    teachers = models.ManyToManyField(TeacherProfile, through='ClassroomTeacher')

    def __str__(self):
        return f"{self.grade} - {self.class_name}"


class ClassroomTeacher(models.Model):
    """
    Intermediate model for the many-to-many relationship between Classroom and TeacherProfile.
    Additional fields like 'subject' can be added here.
    """
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.teacher.user.get_full_name()} teaches {self.classroom}"


class StudentProfile(models.Model):
    """
    Stores additional information about a student, linked to a User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_number = models.CharField(max_length=50, unique=True, db_index=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT)
    birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    def __str__(self):
        return self.user.get_full_name()


class Parent(models.Model):
    """
    Represents a parent or guardian.
    """
    parent_name = models.CharField(max_length=255)
    phone_number = PhoneNumberField()

    def __str__(self):
        return self.parent_name


class ParentStudentRelationship(models.Model):
    """
    Intermediate model representing the relationship between Parents and Students.
    """
    RELATIONSHIP_CHOICES = [
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Guardian', 'Guardian'),
        ('Other', 'Other'),
    ]
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    relationship = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)

    def __str__(self):
        return f"{self.parent.parent_name} - {self.relationship} of {self.student.user.get_full_name()}"
