import json
import urllib

from flask import render_template, url_for, redirect, request, abort
from flask.ext.flask_login import current_user, login_required, login_user, logout_user
from flask_cache import Cache
from google.appengine.api import mail, urlfetch
from google.appengine.ext import db, ndb

from application import app
from application.forms import LoginForm
from application.models import *


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


@login_required
def home():
    if current_user.user_type == 'student':
        return studenthome()

    elif current_user.user_type == 'lecturer':
        return lecturerhome()

    else:
        raise RuntimeError('Something is horribly wrong.')


@login_required
def studenthome():
    if current_user.user_type != 'student':
        return 403

    student = Student.query().filter(Student.user == current_user.key).get()
    courses = ndb.get_multi(student.courses)
    return render_template('studenthome.haml', student=student, courses=courses)


@login_required
def lecturerhome():
    if current_user.user_type != 'lecturer':
        return 403

    lecturer = Lecturer.query().filter(Lecturer.user == current_user.key).get()
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
        return redirect(url_for('home'))

    return render_template('login.haml', form=form)


@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@login_required
def survey(course_key):
    try:
        course = ndb.Key(urlsafe=course_key).get()

    except db.BadKeyError:
        course = None

    if course is None:
        return abort(404)

    if request.method == 'POST':
        lecturer = course.lecturer.get()
        survey = Survey(
            parent=course.key, participant=current_user.key)
        survey.put()
        answers = []
        questions = ndb.get_multi(
            [ndb.Key(urlsafe=question) for question in request.form.keys()])
        for question, answer in zip(questions, request.form.values()):
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
    user1 = User.create('student', 'password', 'student')
    s = Student(name='K Leyow', email_address='kleyow@gmail.com',
                user=user1.key)

    user2 = User.create('lecturer', 'password', 'lecturer')
    l = Lecturer(name='Jimmy', title='Dr', user=user2.key)

    c = Course(name='test')
    ndb.put_multi([l, c])
    cl = Class(course=c.key, lecturer=l.key)
    cl.put()
    s.courses = [cl.key]
    l.courses = [cl.key]
    ndb.put_multi([s, l])

    with open('application/questions.txt') as f:
        questions = []
        for number, line in enumerate(f.readlines()):
            question_type, dimension, question = line.split('|')
            questions.append(Question(question_type=question_type,
                                    dimension=dimension,
                                    question=question,
                                    is_active=True,
                                    number=number + 1))
    ndb.put_multi(questions)
    return 'Done.'


def sentiment_analysis():
    text = request.POST.get('text')
    if text is None:
        return

    try:
        answer = ndb.Key(urlsafe=request.POST.get('answer_key', ''))

    except db.BadKeyError:
        answer = None

    if answer is None:
        return

    response = urlfetch.fetch(
        'http://text-processing.com/api/sentiment',
        payload=urllib.urlencode({'text': text}),
        method=urlfetch.POST)

    # If we've been throttled, just give up and die
    if response.status_code == 503:
        return

    elif response.status_code != 200:
        raise Exception('Retry task')

    sentiment = json.loads(response.content)
    answer.sentiment = sentiment['label']
    answer.put()


def warmup():
    """App Engine warmup handler
    """
    return ''
