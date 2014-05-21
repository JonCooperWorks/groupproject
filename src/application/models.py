"""
models.py

App Engine datastore models

"""
from datetime import date

from google.appengine.ext import ndb
from webapp2_extras.security import generate_password_hash, check_password_hash


class User(ndb.Model):
    username = ndb.StringProperty()
    password_hash = ndb.StringProperty()
    user_type = ndb.StringProperty(choices=['student', 'lecturer', 'admin'])

    @classmethod
    def create(cls, username, password, user_type):
        user = cls(username=username,
                   password_hash=generate_password_hash(password),
                   user_type=user_type)
        user.put()
        return user

    @classmethod
    def authenticate(cls, username, password):
        user = cls.query().filter(cls.username == username).get()
        if user is None:
            return None

        if check_password_hash(password, user.password_hash):
            return user

        return None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        return self.put()

    def get_id(self):
        return self.key.urlsafe()

    def is_authenticated(self):
        return True


class Lecturer(ndb.Model):
    user = ndb.KeyProperty()
    email_address = ndb.StringProperty()
    name = ndb.StringProperty()
    title = ndb.StringProperty()
    department = ndb.KeyProperty()
    courses = ndb.KeyProperty(repeated=True)

    def get_department(self):
        department = Department.query().filter(Department.head_of_department == self.key).get()
        return department

    def get_faculty(self):
        faculty = Faculty.query(Faculty.head_of_faculty == self.key).get()
        return faculty

    def get_school(self):
        school = School.query(School.principal == self.key).get()
        return school

class Student(ndb.Model):
    user = ndb.KeyProperty()
    name = ndb.StringProperty()
    email_address = ndb.StringProperty()
    dob = ndb.DateProperty()
    gender = ndb.StringProperty(choices=['M', 'F'])
    status = ndb.StringProperty(choices=['FT', 'PT'])
    year = ndb.IntegerProperty()
    courses = ndb.KeyProperty(repeated=True)

    def calculate_age(self):
        today = date.today()
        return today.year - self.dob.year - (
            (today.month, today.day) < (self.dob.month, self.dob.day))

class School(ndb.Model):
    name = ndb.StringProperty()
    principal = ndb.KeyProperty(kind=Lecturer)

class Faculty(ndb.Model):
    name = ndb.StringProperty()
    school = ndb.KeyProperty(kind=School)
    head_of_faculty = ndb.KeyProperty(kind=Lecturer)

class Department(ndb.Model):
    name = ndb.StringProperty()
    faculty = ndb.KeyProperty(kind=Faculty)
    head_of_department = ndb.KeyProperty(kind=Lecturer)


class Course(ndb.Model):
    name = ndb.StringProperty()
    code = ndb.StringProperty()
    start_date = ndb.DateProperty()
    end_date = ndb.DateProperty()
    department = ndb.KeyProperty(kind=Department)
    faculty = ndb.KeyProperty(kind=Faculty)
    total_students = ndb.IntegerProperty(default=0)


class Class(ndb.Model):
    course = ndb.KeyProperty(kind=Course)
    lecturer = ndb.KeyProperty(kind=Lecturer)


class Survey(ndb.Model):
    title = ndb.StringProperty()
    description = ndb.StringProperty()
    max_scale = ndb.IntegerProperty(default=5)


class Question(ndb.Model):
    question_type = ndb.StringProperty(choices=['closed', 'open', 'peer'])
    question = ndb.StringProperty()
    number = ndb.IntegerProperty()
    is_active = ndb.BooleanProperty()
    dimension = ndb.StringProperty()

    @classmethod
    def get_active(cls):
        return cls.query().filter(cls.is_active == True).order(cls.number)


class StudentSurvey(ndb.Model):
    participant = ndb.KeyProperty(kind=User)


class Answer(ndb.Model):
    question = ndb.KeyProperty(kind=Question)
    string_value = ndb.StringProperty()
    int_value = ndb.IntegerProperty()
    sentiment = ndb.StringProperty()
    survey = ndb.KeyProperty(kind=Survey)


class StudentCourse(ndb.Model):
    email_address = ndb.StringProperty()
    courses = ndb.StringProperty(repeated=True)
