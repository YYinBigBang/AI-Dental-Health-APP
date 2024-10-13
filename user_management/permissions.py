from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import StudentProfile, ParentStudentRelationship


class IsSuperuser(BasePermission):
    """Allows access only to superusers."""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsTeacher(BasePermission):
    """Allows access only to teachers (users linked to TeacherProfile)."""
    def has_permission(self, request, view):
        return hasattr(request.user, 'teacherprofile')


class IsStudent(BasePermission):
    """Allows access only to students (users linked to StudentProfile)."""
    def has_permission(self, request, view):
        return hasattr(request.user, 'studentprofile')


class IsParent(BasePermission):
    """Allows access only to parents (users linked to Parent profile)."""
    def has_permission(self, request, view):
        return hasattr(request.user, 'parent')


class CanManageClassroom(BasePermission):
    """Allows access to teachers who are managing the classroom."""
    def has_object_permission(self, request, view, obj):
        # Only allow teachers who are assigned to the classroom to manage it
        return request.user.teacherprofile in obj.teachers.all()


class CanManageStudents(BasePermission):
    """Allows access to teachers to manage students in their classroom."""
    def has_object_permission(self, request, view, obj):
        # Check if the student is in a classroom that the teacher manages
        teacher = request.user.teacherprofile
        return obj.classroom.teachers.filter(id=teacher.id).exists()


class CanManageParents(BasePermission):
    """Allows teachers to manage parents of students in their classroom."""
    def has_permission(self, request, view):
        # Only teachers can manage parents
        return hasattr(request.user, 'teacherprofile')

    def has_object_permission(self, request, view, obj):
        # Check if the parent is related to any student in the teacher's classrooms
        teacher = request.user.teacherprofile
        student_ids = StudentProfile.objects.filter(
            classroom__teachers=teacher
        ).values_list('id', flat=True)
        related_parent_ids = ParentStudentRelationship.objects.filter(
            student_id__in=student_ids
        ).values_list('parent_id', flat=True)
        return obj.id in related_parent_ids


class CanManageParentStudentRelationship(BasePermission):
    """Allows teachers to manage parent-student relationships for students in their classroom."""
    def has_permission(self, request, view):
        # Only teachers can manage parent-student relationships
        return hasattr(request.user, 'teacherprofile')

    def has_object_permission(self, request, view, obj):
        # Check if the student in the relationship is in the teacher's classroom
        teacher = request.user.teacherprofile
        return obj.student.classroom.teachers.filter(id=teacher.id).exists()


class IsOwner(BasePermission):
    """Allows access only to the owner of the profile (Student or User)."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

