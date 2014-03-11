import json

from flask import render_template, url_for, redirect
from flask_cache import Cache
from google.appengine.api import mail

from application import app
from application.forms import LoginForm
from application.models import User
from application.models import Question, Student


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
        return redirect(url_for('survey'))
    return render_template('login.haml', form=form)


def survey():
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


def warmup():
    """App Engine warmup handler
    """
    return ''
