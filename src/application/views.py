import json

from flask import render_template, url_for, redirect, request
from flask.ext.flask_login import login_required, login_user
from flask_cache import Cache
from google.appengine.api import mail
from google.appengine.ext import ndb

from application import app
from application.forms import LoginForm
from application.models import User
from application.models import Question, Student, Answer


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


def home():
    return redirect(url_for('login'))


def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user is None:
            return render_template('login.haml',
                                   form=form,
                                   error='Invalid login')

        login_user(user, force=True)
        return redirect(url_for('survey'))
    return render_template('login.haml', form=form)


@login_required
def survey():
    if request.method == 'POST':
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
                    Answer(question=question.key, int_value=int(answer)))

            else:
                answers.append(
                    Answer(question=question.key, string_value=answer))

        ndb.put_multi(answers)

        # TODO: Redirect them somewhere
        return redirect(url_for('login'))

    questions = Question.get_active()
    return render_template('survey.haml', questions=questions)


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
        html = render_template('email/survey_email.haml',student=student)

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

def populatequestions():
    file=open("application/questions.txt",'r')
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


def populatestudents():
    student = Student(name='K Leyow',
                      email_address='kleyow@gmail.com')
    student.put()

def populateusers():
    user = User()
    user.create('user', 'password')

def warmup():
    """App Engine warmup handler
    """
    return ''
