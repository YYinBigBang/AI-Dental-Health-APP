from django.contrib import admin
from .models import (
    School, TeacherProfile, Classroom, StudentProfile,
    Parent, ParentStudentRelationship
)

admin.site.register(School)
admin.site.register(TeacherProfile)
admin.site.register(Classroom)
admin.site.register(StudentProfile)
admin.site.register(Parent)
admin.site.register(ParentStudentRelationship)
