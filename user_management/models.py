
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
    """Custom user model that extends Django's AbstractUser."""
    # username will be used as the user ID, and it is unique.
    full_name = models.CharField(max_length=32, unique=False)  # full name of the user
    line_id = models.CharField(max_length=32, unique=False, blank=True, null=True)

    def __str__(self):
        return self.username


class School(models.Model):
    """stores information about a school."""
    school_code = models.CharField(max_length=64, unique=True)
    school_name = models.CharField(max_length=32)
    school_address = models.CharField(max_length=128)

    def __str__(self):
        return self.school_name


class TeacherProfile(models.Model):
    """Stores additional information about a teacher, linked to a User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birth = models.DateField()
    phone_number = PhoneNumberField()

    def __str__(self):
        return self.user.username


class Classroom(models.Model):
    """Represents a classroom, which can have multiple teachers and students."""
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    grade = models.CharField(max_length=8)
    class_name = models.CharField(max_length=24)
    teachers = models.ManyToManyField(TeacherProfile, through='ClassroomTeacher')

    def __str__(self):
        return f"{self.grade} - {self.class_name}"

    class Meta:
        unique_together = (('school', 'grade', 'class_name'),)


class ClassroomTeacher(models.Model):
    """Intermediate model for the many-to-many relationship between Classroom and TeacherProfile."""
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.teacher.user.username} teaches {self.classroom}"

    class Meta:
        unique_together = (('classroom', 'teacher'),)


class StudentProfile(models.Model):
    """Stores additional information about a student, linked to a User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=24, db_index=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT)
    birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    def __str__(self):
        return self.user.username

    class Meta:
        # Sets of field names that, taken together, must be unique
        unique_together = (('student_id', 'school'),)


class Parent(models.Model):
    """Represents a parent or guardian."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent_name = models.CharField(max_length=255)
    phone_number = PhoneNumberField()

    def __str__(self):
        return self.parent_name


class ParentStudentRelationship(models.Model):
    """Intermediate model representing the relationship between Parents and Students."""
    RELATIONSHIP_CHOICES = [
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Guardian', 'Guardian'),
        ('Other', 'Other'),
    ]
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    relationship = models.CharField(max_length=12, choices=RELATIONSHIP_CHOICES)

    def __str__(self):
        return f"{self.parent.parent_name} - {self.relationship} of {self.student.user.username}"

    class Meta:
        unique_together = (('parent', 'student', 'relationship'),)

