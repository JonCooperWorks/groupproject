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

def studenthome():
    user = current_user
    student = Student.query().filter(Student.user == user.key).get()
    courses = ndb.get_multi(student.courses)
    return render_template('studenthome.haml', student=student, courses=courses)

def lecturerhome():
    user = current_user
    lecturer = Lecturer.query().filter(Lecturer.user == user.key).get()
    courses = ndb.get_multi(lecturer.courses)
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
def survey(course_key):
    course = (ndb.Key(urlsafe=course_key)).get()

    if course is None:
        return abort(404)

    if request.method == 'POST':
        lecturer = course.lecturer.get()
        survey = Survey(course=course.key, lecturer=lecturer.key, participant=current_user.key)
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
        course=course)

def analysis():
    return render_template('analysistest.haml')


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
    ndb.put_multi([l, c])
    cl = Class(course=c.key, lecturer=l.key)
    cl.put()

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
    s.courses.append(cl.key)
    l.courses.append(cl.key)
    s.put()
    l.put()
    return "Done."

def warmup():
    """App Engine warmup handler
    """
    return ''
