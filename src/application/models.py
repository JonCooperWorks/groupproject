"""
models.py

App Engine datastore models

"""


from google.appengine.ext import ndb


class User(ndb.Model):
    username = ndb.StringProperty()
    password_hash = ndb.StringProperty()


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
    head_of_department = ndb.StringProperty()


class Lecturer(ndb.Model):
    user = ndb.KeyProperty()
    name = ndb.StringProperty()
    title = ndb.StringProperty()
    department = ndb.KeyProperty()


class Course(ndb.Model):
    name = ndb.StringProperty()
    start_date = ndb.DateProperty()
    end_date = ndb.DateProperty()
    department = ndb.KeyProperty()
    faculty = ndb.KeyProperty()


class Enrollment(ndb.Model):
    student = ndb.KeyProperty()
    course = ndb.KeyProperty()


class Question(ndb.Model):
    question_type = ndb.StringProperty(choices=['closed', 'open'])
    question = ndb.StringProperty()
    number = ndb.IntegerProperty()
    is_active = ndb.BooleanProperty()
