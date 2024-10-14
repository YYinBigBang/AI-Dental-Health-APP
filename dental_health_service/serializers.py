
from rest_framework import serializers
from .models import TeethCleaningRecord


class TeethCleaningRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeethCleaningRecord
        fields = '__all__'
        read_only_fields = ['date_time']
