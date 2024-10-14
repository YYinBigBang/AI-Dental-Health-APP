
from django.db import models
from user_management.models import StudentProfile


class TeethCleaningRecord(models.Model):
    """Represents a record of a student's teeth cleaning."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    # Automatically set to the current date and time when created.
    date_time = models.DateTimeField(auto_now_add=True)
    images_path = models.CharField(max_length=255, unique=True)
    dental_plaque_count = models.IntegerField()

    class Meta:
        unique_together = ('student', 'date_time')

    def __str__(self):
        return f"{self.student.user.full_name} - {self.date_time}"
