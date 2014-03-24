import json

from flask import render_template, url_for, redirect, request, abort
from flask.ext.flask_login import current_user, login_required, login_user
from flask_cache import Cache
from google.appengine.api import mail
from google.appengine.ext import db, ndb

from application import app
from application.forms import LoginForm
from application.models import *


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


def home():
    return redirect(url_for('login'))

def getlecturer(course_key, student_key):
    course_key=course_key
    course = Course.query().filter(Course.key == course_key).get()
    lecturer = course.lecturer
    return redirect(url_for('survey', lecturer_key=lecturer.key, course_key=course_key))

def studenthome():
    user = current_user
    student = Student.query().filter(Student.user == user.key).get()

    for key in student.courses:
        courses = []
        course = Course.query().filter(Course.key == key).get()
        courses.append(course)

    return render_template('studenthome.haml', student=student, courses=courses)

def lecturerhome():
    user = current_user
    lecturer = Lecturer.query().filter(Lecturer.user == user.key).get()

    for key in lecturer.courses:
        courses = []
        course = Course.query().filter(Course.key == key).get()
        courses.append(course)

    return render_template('lecturerhome.haml', lecturer=lecturer, courses=courses)

def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user is None:
            return render_template('login.haml',
                                   form=form,
                                   error='Invalid login')

        login_user(user, force=True)

        if user.user_type=='student':
            return redirect(url_for('studenthome'))

        if user.user_type=='lecturer':
            return redirect(url_for('lecturerhome'))

    return render_template('login.haml', form=form)


@login_required
def survey(lecturer_key, course_key, student_key):
    lecturer_key, course_key, student_key = (ndb.Key(urlsafe=lecturer_key),
                                             ndb.Key(urlsafe=course_key),
                                             ndb.Key(urlsafe=student_key))
    try:
        lecturer, course, student = ndb.get_multi([lecturer_key, course_key, student_key])

    except db.BadKeyError:
        lecturer, course, student = None, None

    if None in (lecturer, course, student):
        return abort(404)

    if request.method == 'POST':
        survey = Survey(course=course.key, lecturer=lecturer.key, participant=student.key)
        survey.put()
        answers = []
        for question, answer in request.form.items():
            # TODO: Assign each question to a Survey object.
            # This can only be done once we tie each survey to a course, and
            # set up the entity hierarchy properly.
            question = ndb.Key(urlsafe=question).get()
            if question is None:
                continue

            if question.question_type == 'closed':
                answers.append(
                    Answer(question=question.key,
                           int_value=int(answer),
                           parent=survey.key))

            else:
                answers.append(
                    Answer(question=question.key,
                           string_value=answer,
                           parent=survey.key))

        ndb.put_multi(answers)

        # TODO: Redirect them somewhere
        return redirect(url_for('studenthome'))

    questions = Question.get_active()
    return render_template(
        'survey.haml',
        questions=questions,
        lecturer_key=lecturer_key.urlsafe(),
        course_key=course_key.urlsafe())


def analysis():
    return render_template('analysis.haml')


def signup():
    return render_template('signup.haml')


def landing():
    return render_template('landing.haml')


def notify_students():
    students = Student.query()

    for student in students:
        sender = 'surveymailer450@gmail.com'
        subject = 'Course Review Survey'
        html = render_template('email/survey_email.haml', student=student)

        mail_kwargs = {'html': html, 'body': 'TODO.txt',
                       'to': student.email_address,
                       'sender': sender, 'subject': subject}
        mail.send_mail(**mail_kwargs)

    return json.dumps({'status': 'OK'})


# Handlersfor testing styling.
def analysistest():
    return render_template('analysistest.haml')


def studenttestview():
    return render_template('studenttestview.haml')


def lecturertestview():
    return render_template('lecturertestview.haml')


def populate():
    user1 = User().createstudent('student', 'password')
    s = Student(name='K Leyow', email_address='kleyow@gmail.com',
                user=user1.key)

    user2 = User().createlecturer('lecturer', 'password')
    l = Lecturer(name='Jimmy', title='Dr', user=user2.key)

    c = Course(name='test')

    file = open("application/questions.txt", 'r')
    number = 0
    for line in file:
        number += 1
        parsed_line = line.split('|')
        question = Question(question_type=parsed_line[0],
                            dimension=parsed_line[1],
                            question=parsed_line[2],
                            is_active=True,
                            number=number)
        question.put()

    s.put()
    l.put()
    c.put()
    s.courses.append(c.key)
    l.courses.append(c.key)
    s.put()
    return "Done."

def warmup():
    """App Engine warmup handler
    """
    return ''
