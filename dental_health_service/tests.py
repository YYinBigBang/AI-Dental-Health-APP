from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from user_management.models import (
    School,
    TeacherProfile,
    Classroom,
    StudentProfile,
    Parent,
    ParentStudentRelationship
)
from .models import TeethCleaningRecord
from unittest.mock import patch
from io import BytesIO

User = get_user_model()


class TeethCleaningRecordModelTests(APITestCase):
    def setUp(self):
        # Create a student user and associated StudentProfile
        self.user = User.objects.create_user(
            username='studentuser',
            password='testpass123',
            full_name='Student User'
        )
        self.school = School.objects.create(
            school_code='SCH001',
            school_name='Test School',
            school_address='123 Test St'
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            grade='Grade 1',
            class_name='Class A'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            student_id='S123',
            school=self.school,
            classroom=self.classroom,
            birth='2010-01-01',
            gender='F'
        )

    def test_create_teeth_cleaning_record(self):
        record = TeethCleaningRecord.objects.create(
            student=self.student_profile,
            images_path='path/to/image.png',
            dental_plaque_count=5
        )
        self.assertEqual(record.student, self.student_profile)
        self.assertEqual(record.dental_plaque_count, 5)
        self.assertIsNotNone(record.date_time)

    def test_teeth_cleaning_record_str(self):
        record = TeethCleaningRecord.objects.create(
            student=self.student_profile,
            images_path='path/to/image.png',
            dental_plaque_count=5
        )
        expected_str = f"{self.student_profile.user.full_name} - {record.date_time}"
        self.assertEqual(str(record), expected_str)

    def test_unique_together_constraint(self):
        # Attempt to create a duplicate record with the same student and date_time
        record1 = TeethCleaningRecord.objects.create(
            student=self.student_profile,
            images_path='path/to/image1.png',
            dental_plaque_count=5
        )
        with self.assertRaises(Exception):
            TeethCleaningRecord.objects.create(
                student=self.student_profile,
                date_time=record1.date_time,
                images_path='path/to/image2.png',
                dental_plaque_count=3
            )


class PublicEndpointTests(APITestCase):
    def test_test_endpoint(self):
        url = reverse('test_endpoint')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Hi there, API is working~"})


class AnalyzeImageTests(APITestCase):
    def test_analyze_image_no_image(self):
        url = reverse('analyze_image')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "No image provided"})

    @patch('dental_health_service.views.DentalPlaqueAnalysis.analyze_dental_plaque')
    def test_analyze_image_with_image(self, mock_analyze):
        mock_analyze.return_value = 'Analysis successful'
        url = reverse('analyze_image')
        image_file = BytesIO(b'test image content')
        image_file.name = 'test_image.png'
        response = self.client.post(url, {'image': image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Analysis successful')

    @patch('dental_health_service.views.DentalPlaqueAnalysis.analyze_dental_plaque')
    def test_analyze_image_exception(self, mock_analyze):
        mock_analyze.side_effect = Exception('Analysis failed')
        url = reverse('analyze_image')
        image_file = BytesIO(b'test image content')
        image_file.name = 'test_image.png'
        response = self.client.post(url, {'image': image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "An error occurred during analysis"})


class AuthenticatedEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_test_jwt_permission_without_auth(self):
        url = reverse('test_jwt_permission')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_test_jwt_permission_with_auth(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('test_jwt_permission')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Greetings, you have permission to access this endpoint"})


class TeethCleaningRecordAPITests(APITestCase):
    def setUp(self):
        # Create a student user and associated StudentProfile
        self.student_user = User.objects.create_user(
            username='studentuser',
            password='testpass123',
            full_name='Student User'
        )
        self.school = School.objects.create(
            school_code='SCH001',
            school_name='Test School',
            school_address='123 Test St'
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            grade='Grade 1',
            class_name='Class A'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id='S123',
            school=self.school,
            classroom=self.classroom,
            birth='2010-01-01',
            gender='F'
        )

        # Create a parent user and associated Parent
        self.parent_user = User.objects.create_user(
            username='parentuser',
            password='testpass123',
            full_name='Parent User'
        )
        self.parent = Parent.objects.create(
            user=self.parent_user,
            parent_name='Parent Name',
            phone_number='+1234567890'
        )
        ParentStudentRelationship.objects.create(
            parent=self.parent,
            student=self.student_profile,
            relationship='Mother'
        )

        # Create a teacher user and associated TeacherProfile
        self.teacher_user = User.objects.create_user(
            username='teacheruser',
            password='testpass123',
            full_name='Teacher User'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            school=self.school,
            gender='M',
            birth='1980-01-01',
            phone_number='+1234567890'
        )
        self.classroom.teachers.add(self.teacher_profile)

        # Create a TeethCleaningRecord
        self.record = TeethCleaningRecord.objects.create(
            student=self.student_profile,
            images_path='path/to/image.png',
            dental_plaque_count=5
        )

    def test_student_can_view_own_records(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teeth_cleaning_record_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_parent_can_view_child_records(self):
        self.client.force_authenticate(user=self.parent_user)
        url = reverse('teeth_cleaning_record_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_teacher_can_view_student_records(self):
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teeth_cleaning_record_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthorized_user_cannot_view_records(self):
        unauthorized_user = User.objects.create_user(
            username='unauthuser',
            password='testpass123',
            full_name='Unauthorized User'
        )
        self.client.force_authenticate(user=unauthorized_user)
        url = reverse('teeth_cleaning_record_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_create_own_record(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teeth_cleaning_record_list')
        data = {
            'student': self.student_profile.id,
            'images_path': 'path/to/new_image.png',
            'dental_plaque_count': 3
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_create_record_for_other_student(self):
        self.client.force_authenticate(user=self.student_user)
        # Create another student
        another_student_user = User.objects.create_user(
            username='studentuser2',
            password='testpass123',
            full_name='Student User 2'
        )
        another_student_profile = StudentProfile.objects.create(
            user=another_student_user,
            student_id='S124',
            school=self.school,
            classroom=self.classroom,
            birth='2010-02-02',
            gender='M'
        )
        url = reverse('teeth_cleaning_record_list')
        data = {
            'student': another_student_profile.id,
            'images_path': 'path/to/new_image.png',
            'dental_plaque_count': 4
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_create_record_for_student(self):
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teeth_cleaning_record_list')
        data = {
            'student': self.student_profile.id,
            'images_path': 'path/to/new_image.png',
            'dental_plaque_count': 2
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_can_update_own_record(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teeth_cleaning_record_detail', args=[self.record.id])
        data = {
            'student': self.student_profile.id,
            'images_path': 'path/to/updated_image.png',
            'dental_plaque_count': 1
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dental_plaque_count'], 1)

    def test_student_cannot_update_others_record(self):
        # Create another student's record
        another_student_user = User.objects.create_user(
            username='studentuser2',
            password='testpass123',
            full_name='Student User 2'
        )
        another_student_profile = StudentProfile.objects.create(
            user=another_student_user,
            student_id='S124',
            school=self.school,
            classroom=self.classroom,
            birth='2010-02-02',
            gender='M'
        )
        another_record = TeethCleaningRecord.objects.create(
            student=another_student_profile,
            images_path='path/to/another_image.png',
            dental_plaque_count=4
        )
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teeth_cleaning_record_detail', args=[another_record.id])
        data = {
            'student': another_student_profile.id,
            'images_path': 'path/to/updated_image.png',
            'dental_plaque_count': 1
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_delete_own_record(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teeth_cleaning_record_detail', args=[self.record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_student_cannot_delete_others_record(self):
        # Create another student's record
        another_student_user = User.objects.create_user(
            username='studentuser2',
            password='testpass123',
            full_name='Student User 2'
        )
        another_student_profile = StudentProfile.objects.create(
            user=another_student_user,
            student_id='S124',
            school=self.school,
            classroom=self.classroom,
            birth='2010-02-02',
            gender='M'
        )
        another_record = TeethCleaningRecord.objects.create(
            student=another_student_profile,
            images_path='path/to/another_image.png',
            dental_plaque_count=4
        )
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teeth_cleaning_record_detail', args=[another_record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_update_student_record(self):
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teeth_cleaning_record_detail', args=[self.record.id])
        data = {
            'student': self.student_profile.id,
            'images_path': 'path/to/updated_image.png',
            'dental_plaque_count': 10
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dental_plaque_count'], 10)

    def test_teacher_can_delete_student_record(self):
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teeth_cleaning_record_detail', args=[self.record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_parent_cannot_create_record_for_child(self):
        self.client.force_authenticate(user=self.parent_user)
        url = reverse('teeth_cleaning_record_list')
        data = {
            'student': self.student_profile.id,
            'images_path': 'path/to/new_image.png',
            'dental_plaque_count': 3
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_parent_cannot_update_child_record(self):
        self.client.force_authenticate(user=self.parent_user)
        url = reverse('teeth_cleaning_record_detail', args=[self.record.id])
        data = {
            'student': self.student_profile.id,
            'images_path': 'path/to/updated_image.png',
            'dental_plaque_count': 7
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_parent_cannot_delete_child_record(self):
        self.client.force_authenticate(user=self.parent_user)
        url = reverse('teeth_cleaning_record_detail', args=[self.record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_record_not_found(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teeth_cleaning_record_detail', args=[999])  # Non-existent ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_record_unauthorized_access(self):
        # Another student trying to access self.student_user's record
        another_student_user = User.objects.create_user(
            username='studentuser2',
            password='testpass123',
            full_name='Student User 2'
        )
        self.client.force_authenticate(user=another_student_user)
        url = reverse('teeth_cleaning_record_detail', args=[self.record.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_records_no_authorized_students(self):
        # Create a user with no associated profiles
        unauthorized_user = User.objects.create_user(
            username='unauthuser',
            password='testpass123',
            full_name='Unauthorized User'
        )
        self.client.force_authenticate(user=unauthorized_user)
        url = reverse('teeth_cleaning_record_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'Not authorized to view records.'})


class ImageUploadDownloadTests(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='studentuser',
            password='testpass123',
            full_name='Student User'
        )
        self.client.force_authenticate(user=self.student_user)

    def test_upload_image_no_file(self):
        url = reverse('upload_image')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "No image provided"})

    def test_upload_image_with_file(self):
        url = reverse('upload_image')
        image_file = BytesIO(b'test image content')
        image_file.name = 'test_image.png'
        response = self.client.post(url, {'image': image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"message": "Image uploaded successfully"})

    def test_download_existing_image(self):
        # First, upload an image
        upload_url = reverse('upload_image')
        image_file = BytesIO(b'test image content')
        image_file.name = 'test_image.png'
        self.client.post(upload_url, {'image': image_file}, format='multipart')

        # Now, download the image
        download_url = reverse('download_image', args=['test_image.png'])
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_download_nonexistent_image(self):
        download_url = reverse('download_image', args=['nonexistent_image.png'])
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetAnalysisResultTests(APITestCase):
    def test_get_analysis_result_valid(self):
        # Simulate existing analysis images
        from django.conf import settings
        import os
        folder_name = 'test_folder'
        valid_image_types = ['teeth_range', 'teeth_range_detect']
        save_path = os.path.join(settings.MEDIA_ROOT, 'dental_plaque_analysis', folder_name)
        os.makedirs(save_path, exist_ok=True)
        for image_name in valid_image_types:
            with open(os.path.join(save_path, f'{image_name}.png'), 'wb') as f:
                f.write(b'test image content')

        url = reverse('get_analysis_result', args=['teeth_range', folder_name])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_get_analysis_result_invalid_image_type(self):
        url = reverse('get_analysis_result', args=['invalid_type', 'some_folder'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_analysis_result_nonexistent_image(self):
        url = reverse('get_analysis_result', args=['teeth_range', 'nonexistent_folder'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

