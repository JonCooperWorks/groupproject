"""
models.py

App Engine datastore models

"""


from google.appengine.ext import ndb
from webapp2_extras.security import generate_password_hash, check_password_hash


class User(ndb.Model):
    username = ndb.StringProperty()
    password_hash = ndb.StringProperty()

    @classmethod
    def create(cls, username, password):
        user = cls(username=username,
                   password_hash=generate_password_hash(password))
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


class Student(ndb.Model):
    user = ndb.KeyProperty()
    name = ndb.StringProperty()
    email_address = ndb.StringProperty()
    dob = ndb.DateProperty()
    gender = ndb.StringProperty(choices=['M', 'F'])
    status = ndb.StringProperty(choices=['FT', 'PT'])
    year = ndb.IntegerProperty()


class Department(ndb.Model):
    name = ndb.StringProperty()
    faculty = ndb.KeyProperty()


class Faculty(ndb.Model):
    name = ndb.StringProperty()
    head_of_department = ndb.KeyProperty(kind=Lecturer)


class Lecturer(ndb.Model):
    user = ndb.KeyProperty()
    name = ndb.StringProperty()
    title = ndb.StringProperty()
    department = ndb.KeyProperty()


class Course(ndb.Model):
    name = ndb.StringProperty()
    start_date = ndb.DateProperty()
    end_date = ndb.DateProperty()
    department = ndb.KeyProperty(kind=Department)
    faculty = ndb.KeyProperty(kind=Faculty)
    total_students = ndb.IntegerProperty()


class Enrollment(ndb.Model):
    student = ndb.KeyProperty(kind=Student)
    course = ndb.KeyProperty(kind=Course)


class Question(ndb.Model):
    question_type = ndb.StringProperty(choices=['closed', 'open'])
    question = ndb.StringProperty()
    number = ndb.IntegerProperty()
    is_active = ndb.BooleanProperty()

    @classmethod
    def get_active(cls):
        return cls.query().filter(cls.is_active == True)


class Survey(ndb.Model):
    participant = ndb.KeyProperty(kind=Student)
    course = ndb.KeyProperty(kind=Course)
    lecturer = ndb.KeyProperty(kind=Lecturer)
    questions = ndb.KeyProperty(kind=Question, repeated=True)


class Answer(ndb.Model):
    question = ndb.KeyProperty(kind=Question)
    string_value = ndb.StringProperty()
    int_value = ndb.IntegerProperty()
    survey = ndb.KeyProperty(kind=Survey)


