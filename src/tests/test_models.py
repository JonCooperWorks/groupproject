import unittest

from application import models


class UserTestCase(unittest.TestCase):

    def test_defaults(self):
        user = models.User()
        self.assertIsNone(user.username)
        self.assertIsNone(user.password_hash)


class StudentTestCase(unittest.TestCase):

    def test_defaults(self):
        student = models.Student()
        self.assertIsNone(student.user)
        self.assertIsNone(student.name)
        self.assertIsNone(student.email_address)
        self.assertIsNone(student.dob)
        self.assertIsNone(student.gender)
        self.assertIsNone(student.status)
        self.assertIsNone(student.year)


class DepartmentTestCase(unittest.TestCase):

    def test_defaults(self):
        dept = models.Department()
        self.assertIsNone(dept.name)
        self.assertIsNone(dept.faculty)


class FacultyTestCase(unittest.TestCase):

    def test_defaults(self):
        faculty = models.Faculty()
        self.assertIsNone(faculty.name)
        self.assertIsNone(faculty.head_of_department)


class LecturerTestCase(unittest.TestCase):

    def test_defaults(self):
        lecturer = models.Lecturer()
        self.assertIsNone(lecturer.name)
        self.assertIsNone(lecturer.user)
        self.assertIsNone(lecturer.title)
        self.assertIsNone(lecturer.department)


class CourseTestCase(unittest.TestCase):

    def test_defaults(self):
        course = models.Course()
        self.assertIsNone(course.name)
        self.assertIsNone(course.start_date)
        self.assertIsNone(course.end_date)
        self.assertIsNone(course.department)
        self.assertIsNone(course.faculty)


class EnrollmentTestCase(unittest.TestCase):

    def test_defaults(self):
        enrollment = models.Enrollment()
        self.assertIsNone(enrollment.student)
        self.assertIsNone(enrollment.course)


class QuestionTestCase(unittest.TestCase):

    def test_defaults(self):
        question = models.Question()
        self.assertIsNone(question.number)
        self.assertIsNone(question.question)
        self.assertIsNone(question.question_type)
        self.assertIsNone(question.is_active)
