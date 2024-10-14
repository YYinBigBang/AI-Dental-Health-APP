from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from .models import (
    School,
    TeacherProfile,
    Classroom,
    StudentProfile,
    Parent,
    ParentStudentRelationship,
)


class UserModelTests(APITestCase):
    def test_create_user(self):
        user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123',
            full_name='Test User',
            email='testuser@example.com'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))


class SchoolModelTests(APITestCase):
    def test_create_school(self):
        school = School.objects.create(
            school_code='SCH001',
            school_name='Test School',
            school_address='123 Test St'
        )
        self.assertEqual(school.school_name, 'Test School')


class TeacherProfileModelTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='teacheruser',
            password='testpass123',
            full_name='Teacher User',
            email='teacher@example.com'
        )
        self.school = School.objects.create(
            school_code='SCH001',
            school_name='Test School',
            school_address='123 Test St'
        )

    def test_create_teacher_profile(self):
        teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            school=self.school,
            gender='M',
            birth='1980-01-01',
            phone_number='+1234567890'
        )
        self.assertEqual(teacher_profile.user.username, 'teacheruser')


class ClassroomModelTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(
            school_code='SCH001',
            school_name='Test School',
            school_address='123 Test St'
        )

    def test_create_classroom(self):
        classroom = Classroom.objects.create(
            school=self.school,
            grade='Grade 1',
            class_name='Class A'
        )
        self.assertEqual(classroom.grade, 'Grade 1')


class StudentProfileModelTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='studentuser',
            password='testpass123',
            full_name='Student User',
            email='student@example.com'
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

    def test_create_student_profile(self):
        student_profile = StudentProfile.objects.create(
            user=self.user,
            student_id='S123',
            school=self.school,
            classroom=self.classroom,
            birth='2010-01-01',
            gender='F'
        )
        self.assertEqual(student_profile.user.username, 'studentuser')


class ParentModelTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='parentuser',
            password='testpass123',
            full_name='Parent User',
            email='parent@example.com'
        )

    def test_create_parent(self):
        parent = Parent.objects.create(
            user=self.user,
            parent_name='Parent Name',
            phone_number='+1234567890'
        )
        self.assertEqual(parent.user.username, 'parentuser')


class ParentStudentRelationshipModelTests(APITestCase):
    def setUp(self):
        self.parent_user = get_user_model().objects.create_user(
            username='parentuser',
            password='testpass123',
            full_name='Parent User',
            email='parent@example.com'
        )
        self.student_user = get_user_model().objects.create_user(
            username='studentuser',
            password='testpass123',
            full_name='Student User',
            email='student@example.com'
        )
        self.parent = Parent.objects.create(
            user=self.parent_user,
            parent_name='Parent Name',
            phone_number='+1234567890'
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

    def test_create_relationship(self):
        relationship = ParentStudentRelationship.objects.create(
            parent=self.parent,
            student=self.student_profile,
            relationship='Mother'
        )
        self.assertEqual(relationship.parent.parent_name, 'Parent Name')


class UserAuthenticationTests(APITestCase):
    def test_user_signup(self):
        url = reverse('signup')
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'full_name': 'New User',
            'email': 'newuser@example.com'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)

    def test_user_login(self):
        user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)


class TeacherTests(APITestCase):
    def setUp(self):
        # Create a teacher user
        self.user = get_user_model().objects.create_user(
            username='teacheruser',
            password='testpass123',
            full_name='Teacher User'
        )
        self.school = School.objects.create(
            school_code='SCH001',
            school_name='Test School',
            school_address='123 Test St'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.user,
            school=self.school,
            gender='M',
            birth='1980-01-01',
            phone_number='+1234567890'
        )
        self.client = APIClient()
        # Authenticate as teacher
        self.client.force_authenticate(user=self.user)

    def test_get_teacher_profile(self):
        url = reverse('teacherprofile-detail', args=[self.teacher_profile.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_classroom(self):
        url = reverse('classroom-list')
        data = {
            'school': self.school.pk,
            'grade': 'Grade 1',
            'class_name': 'Class A',
            'teachers': [self.teacher_profile.pk]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class StudentTests(APITestCase):
    def setUp(self):
        # Create a teacher and classroom
        self.teacher_user = get_user_model().objects.create_user(
            username='teacheruser',
            password='testpass123',
            full_name='Teacher User'
        )
        self.school = School.objects.create(
            school_code='SCH001',
            school_name='Test School',
            school_address='123 Test St'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            school=self.school,
            gender='M',
            birth='1980-01-01',
            phone_number='+1234567890'
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            grade='Grade 1',
            class_name='Class A'
        )
        self.classroom.teachers.add(self.teacher_profile)
        # Create a student user
        self.student_user = get_user_model().objects.create_user(
            username='studentuser',
            password='testpass123',
            full_name='Student User'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id='S123',
            school=self.school,
            classroom=self.classroom,
            birth='2010-01-01',
            gender='F'
        )
        self.client = APIClient()

    def test_teacher_can_view_students(self):
        # Authenticate as teacher
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('studentprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_student_can_view_own_profile(self):
        # Authenticate as student
        self.client.force_authenticate(user=self.student_user)
        url = reverse('studentprofile-detail', args=[self.student_profile.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_view_others(self):
        # Create another student
        another_user = get_user_model().objects.create_user(
            username='anotherstudent',
            password='testpass123',
            full_name='Another Student'
        )
        another_student = StudentProfile.objects.create(
            user=another_user,
            student_id='S124',
            school=self.school,
            classroom=self.classroom,
            birth='2010-01-01',
            gender='M'
        )
        # Authenticate as first student
        self.client.force_authenticate(user=self.student_user)
        url = reverse('studentprofile-detail', args=[another_student.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ParentTests(APITestCase):
    def setUp(self):
        # Create a parent user
        self.parent_user = get_user_model().objects.create_user(
            username='parentuser',
            password='testpass123',
            full_name='Parent User'
        )
        self.parent = Parent.objects.create(
            user=self.parent_user,
            parent_name='Parent Name',
            phone_number='+1234567890'
        )
        # Create a student and relationship
        self.student_user = get_user_model().objects.create_user(
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
        ParentStudentRelationship.objects.create(
            parent=self.parent,
            student=self.student_profile,
            relationship='Mother'
        )
        self.client = APIClient()

    def test_parent_can_view_own_profile(self):
        # Authenticate as parent
        self.client.force_authenticate(user=self.parent_user)
        url = reverse('parent-detail', args=[self.parent.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_parent_can_view_relationships(self):
        # Authenticate as parent
        self.client.force_authenticate(user=self.parent_user)
        url = reverse('parentstudentrelationship-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class PermissionTests(APITestCase):
    def setUp(self):
        # Create users
        self.teacher_user = get_user_model().objects.create_user(
            username='teacheruser',
            password='testpass123'
        )
        self.student_user = get_user_model().objects.create_user(
            username='studentuser',
            password='testpass123'
        )
        self.parent_user = get_user_model().objects.create_user(
            username='parentuser',
            password='testpass123'
        )
        # Create profiles
        self.school = School.objects.create(
            school_code='SCH001',
            school_name='Test School',
            school_address='123 Test St'
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            school=self.school,
            gender='M',
            birth='1980-01-01',
            phone_number='+1234567890'
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            grade='Grade 1',
            class_name='Class A'
        )
        self.classroom.teachers.add(self.teacher_profile)
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id='S123',
            school=self.school,
            classroom=self.classroom,
            birth='2010-01-01',
            gender='F'
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
        self.client = APIClient()

    def test_student_cannot_access_teacher_endpoints(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teacherprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_parent_cannot_modify_student_profile(self):
        self.client.force_authenticate(user=self.parent_user)
        url = reverse('studentprofile-detail', args=[self.student_profile.pk])
        data = {'full_name': 'New Name'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

