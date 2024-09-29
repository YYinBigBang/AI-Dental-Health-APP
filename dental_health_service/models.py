from django.db import models
from user_management.models import StudentProfile


class TeethCleaningRecord(models.Model):
    """
    Represents a record of a student's teeth cleaning.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    dental_plaque_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'date_time')

    def __str__(self):
        return f"Teeth Cleaning Record for {self.student.user.get_full_name()} on {self.date_time.strftime('%Y-%m-%d')}"
