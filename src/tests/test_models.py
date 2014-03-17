from application import models
from lib import testing


class UserTestCase(testing.TestCase):

    CREDENTIALS = ('username', 'password')

    def test_defaults(self):
        user = models.User()
        self.assertIsNone(user.username)
        self.assertIsNone(user.password_hash)

    def test_create(self):
        user = models.User.create(*self.CREDENTIALS)
        username, password = self.CREDENTIALS
        self.assertEqual(username, user.username)
        self.assertNotEqual(password, user.password_hash)

    def test_authenticate(self):
        models.User.create(*self.CREDENTIALS)
        username, password = self.CREDENTIALS
        user = models.User.authenticate(username, password)
        self.assertIsNotNone(user)
        self.assertEqual(username, user.username)

    def test_authenticate_rejects_bad_password(self):
        models.User.create(*self.CREDENTIALS)
        user = models.User.authenticate('username', 'wrong')
        self.assertIsNone(user)


class StudentTestCase(testing.TestCase):

    def test_defaults(self):
        student = models.Student()
        self.assertIsNone(student.user)
        self.assertIsNone(student.name)
        self.assertIsNone(student.email_address)
        self.assertIsNone(student.dob)
        self.assertIsNone(student.gender)
        self.assertIsNone(student.status)
        self.assertIsNone(student.year)


class DepartmentTestCase(testing.TestCase):

    def test_defaults(self):
        dept = models.Department()
        self.assertIsNone(dept.name)
        self.assertIsNone(dept.faculty)


class FacultyTestCase(testing.TestCase):

    def test_defaults(self):
        faculty = models.Faculty()
        self.assertIsNone(faculty.name)
        self.assertIsNone(faculty.head_of_department)


class LecturerTestCase(testing.TestCase):

    def test_defaults(self):
        lecturer = models.Lecturer()
        self.assertIsNone(lecturer.name)
        self.assertIsNone(lecturer.user)
        self.assertIsNone(lecturer.title)
        self.assertIsNone(lecturer.department)


class CourseTestCase(testing.TestCase):

    def test_defaults(self):
        course = models.Course()
        self.assertIsNone(course.name)
        self.assertIsNone(course.start_date)
        self.assertIsNone(course.end_date)
        self.assertIsNone(course.department)
        self.assertIsNone(course.faculty)


class QuestionTestCase(testing.TestCase):

    def test_defaults(self):
        question = models.Question()
        self.assertIsNone(question.number)
        self.assertIsNone(question.question)
        self.assertIsNone(question.question_type)
        self.assertIsNone(question.is_active)

    def test_is_active(self):
        question = models.Question(is_active=True).put()
        models.Question(is_active=False).put()
        self.assertEqual(1, models.Question.get_active().count())
        self.assertEqual(question, models.Question.get_active().get().key)


class SurveyTestCase(testing.TestCase):

    def test_defaults(self):
        survey = models.Survey()
        self.assertIsNone(survey.participant)
        self.assertIsNone(survey.course)
        self.assertIsNone(survey.lecturer)
        self.assertEqual(0, len(survey.questions))


class AnswerTestCase(testing.TestCase):

    def test_defaults(self):
        answer = models.Answer()
        self.assertIsNone(answer.question)
        self.assertIsNone(answer.string_value)
        self.assertIsNone(answer.survey)
