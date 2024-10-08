from django.test import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import TeacherProfile, StudentProfile, Parent, School, Classroom, ParentStudentRelationship


class RegistrationTestCase(APITestCase):
    def test_teacher_registration(self):
        url = reverse('teacher_signup')
        school = School.objects.create(name="Test School", school_code="123")
        data = {
            "user": {
                "username": "teacher1",
                "email": "teacher1@example.com",
                "password": "strongpassword123"
            },
            "school": school.id,
            "gender": "M",
            "birth": "1980-01-01",
            "phone_number": "1234567890"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_student_registration(self):
        url = reverse('student_signup')
        classroom = Classroom.objects.create(grade="1", class_name="A")
        data = {
            "user": {
                "username": "student1",
                "email": "student1@example.com",
                "password": "strongpassword123"
            },
            "student_number": "S123456",
            "classroom": classroom.id,
            "birth": "2005-06-01",
            "gender": "M"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_parent_registration(self):
        url = reverse('parent_signup')
        data = {
            "user": {
                "username": "parent1",
                "email": "parent1@example.com",
                "password": "strongpassword123"
            },
            "parent_name": "John Doe",
            "phone_number": "9876543210"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class LoginTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='strongpassword123')

    def test_login(self):
        url = reverse('login')
        data = {
            "username": "testuser",
            "password": "strongpassword123"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class TeacherProfileTestCase(APITestCase):
    def setUp(self):
        # Create a teacher user and profile
        self.user = User.objects.create_user(username='teacher1', password='strongpassword123')
        self.school = School.objects.create(name='Test School', school_code="123")
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            school=self.school,
            gender='M',
            birth='1980-01-01',
            phone_number='1234567890'
        )
        # Obtain JWT token
        response = self.client.post(reverse('login'), {
            'username': 'teacher1',
            'password': 'strongpassword123'
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_get_teacher_profile(self):
        url = reverse('teacher_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.teacher_profile.id)

    def test_update_teacher_profile(self):
        url = reverse('teacher_profile')
        data = {
            "phone_number": "1111111111"
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.teacher_profile.refresh_from_db()
        self.assertEqual(self.teacher_profile.phone_number, '1111111111')


class StudentProfileTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student1', password='strongpassword123')
        self.classroom = Classroom.objects.create(grade='1', class_name='A')
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            student_number='S123456',
            classroom=self.classroom,
            birth='2005-06-01',
            gender='M'
        )
        # Obtain JWT token
        response = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'strongpassword123'
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_get_student_profile(self):
        url = reverse('student_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.student_profile.id)


class ParentProfileTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='parent1', password='strongpassword123')
        self.parent = Parent.objects.create(
            user=self.user,
            parent_name='John Doe',
            phone_number='1234567890'
        )
        # Obtain JWT token
        response = self.client.post(reverse('login'), {
            'username': 'parent1',
            'password': 'strongpassword123'
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_get_parent_profile(self):
        url = reverse('parent_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.parent.id)


class ParentStudentViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='parent1', password='strongpassword123')
        self.parent = Parent.objects.create(
            user=self.user,
            parent_name='John Doe',
            phone_number='1234567890'
        )
        self.classroom = Classroom.objects.create(grade='1', class_name='A')
        self.student = StudentProfile.objects.create(
            user=User.objects.create_user(username='student1', password='strongpassword123'),
            student_number='S123456',
            classroom=self.classroom,
            birth='2005-06-01',
            gender='M'
        )
        self.parent_student_relationship = ParentStudentRelationship.objects.create(
            parent=self.parent,
            student=self.student,
            relationship='Father'
        )
        # Obtain JWT token
        response = self.client.post(reverse('login'), {
            'username': 'parent1',
            'password': 'strongpassword123'
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_get_parent_students(self):
        url = reverse('parent_students')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['student'], self.student.id)