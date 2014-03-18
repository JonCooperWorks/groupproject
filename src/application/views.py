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
        subject = 'Course Review Survey'
        body = 'Do your survey'
        mail.send_mail(
            'surveymailer450@gmail.com', student.email_address, subject, body)

    return json.dumps({'status': 'OK'})


# Handlersfor testing styling.
def surveytest():
    return render_template('surveytest.haml')


def analysistest():
    return render_template('analysistest.haml')


def studenttestview():
    return render_template('studenttestview.haml')


def lecturertestview():
    return render_template('lecturertestview.haml')


def warmup():
    """App Engine warmup handler
    """
    return ''

@app.route('/usermake')
def makeuser():
    ls = [
        {'question_type':'closed', 'question':'The lecturer arrived on', 'is_active': True},
        {'question_type':'closed', 'question':'The lecturer was prepared for classes', 'is_active':True},
        {'question_type':'closed', 'question':'The lecturer\'s use of interactive technology ..', 'is_active': True}
    ]
    for l in ls:
        Question(**l).put()

    return 'done'
