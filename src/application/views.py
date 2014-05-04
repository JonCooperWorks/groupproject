import json
import urllib

from flask import render_template, url_for, redirect, request, abort
from flask.ext.flask_login import current_user, login_required, login_user,\
    logout_user
from flask_cache import Cache
from google.appengine.api import mail, urlfetch
from google.appengine.ext import db, deferred, ndb
import keen

from application import app
from application.forms import LoginForm
from application.models import Student, Lecturer, Course, Class, Answer, \
    Question, Survey, User, Faculty, Department


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


@login_required
def home():
    if current_user.user_type == 'student':
        return studenthome()

    elif current_user.user_type == 'lecturer':
        return lecturerhome()

    elif current_user.user_type == 'admin':
        return adminhome()

    else:
        raise RuntimeError('Something is horribly wrong.')


@login_required
def studenthome():
    if current_user.user_type != 'student':
        return 403

    student = Student.query().filter(Student.user == current_user.key).get()
    courses = ndb.get_multi(student.courses)

    for course in courses:
        survey = Survey.query(ancestor=course.key).filter(Survey.participant == current_user.key).get()
        if survey is not None:
            courses.remove(course)

    all_classes = Class.query()
    return render_template(
        'studenthome.haml', student=student, courses=courses,
        all_classes=all_classes)


@login_required
def peerreview():
    if current_user.user_type != 'student':
        return 403

    student = Student.query().filter(Student.user == current_user.key).get()
    courses = ndb.get_multi(student.courses)
    all_classes = Class.query()
    return render_template(
        'peerreview.haml', student=student, courses=courses,
        all_classes=all_classes)


@login_required
def lecturerhome():
    if current_user.user_type != 'lecturer':
        return 403

    lecturer = Lecturer.query().filter(Lecturer.user == current_user.key).get()
    courses = ndb.get_multi(lecturer.courses)
    return render_template(
        'lecturerhome.haml', lecturer=lecturer, courses=courses)


@login_required
def adminhome():
    if current_user.user_type != 'admin':
        return 403

    return render_template('adminhome.haml')


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
        deferred.defer(_send_to_keen, course, answers)
        return redirect(url_for('home'))

    questions = Question.get_active()
    return render_template(
        'survey.haml',
        questions=questions,
        course=course)


def _send_to_keen(course, answers):
    events = []
    for answer in answers:
        question = answer.question.get()
        if answer.string_value != '':
            response = urlfetch.fetch(
                'http://text-processing.com/api/sentiment',
                payload=urllib.urlencode({'text': answer.string_value}),
                method=urlfetch.POST)

            # If we've been throttled, just give up and die
            if response.status_code == 503:
                continue

            elif response.status_code != 200:
                raise deferred.PermanentTaskFailure()

            sentiment = json.loads(response.content)
            answer.sentiment = sentiment['label']
            answer.put()

        lecturer = course.lecturer.get()
        event = {
            'question_key': question.key.urlsafe(),
            'survey_key': answer.key.parent().urlsafe(),
            'course_key': course.key.urlsafe(),
            'question_number': question.number,
            'lecturer': {
                'key': lecturer.key.urlsafe(),
                'name': lecturer.name,
                'department': lecturer.department.get().name,
                'faculty': lecturer.department.get().faculty.get().name,
            },
        }

        if question.question_type == 'closed':
            event['response'] = answer.int_value

        else:
            event['sentiment'] = answer.sentiment

        events.append(event)

    keen.add_events({'answers': events})


def analysis(class_key):
    try:
        class_ = ndb.Key(urlsafe=class_key).get()

    except db.BadKeyError:
        class_ = None

    if class_ is None:
        return abort(404)

    course = class_.course.get()
    lecturer = class_.lecturer.get()
    surveys = Survey.query(ancestor=class_.key)
    return render_template(
        'analysis.haml',
        surveys=surveys,
        course=course,
        lecturer=lecturer,
        class_key=class_key,
        questions=Question.get_active())


def signup():
    return render_template('signup.haml')


def landing():
    return render_template('landing.haml')


@login_required
def notify_students():
    if current_user.user_type != 'admin':
        return 403
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


def query():
    """Custom queries using keen.io as a backend.
    The frontent form must pass values in using the names
        `property_name` - The name of the property you wish to query
        `property_value` - The value of the property being entered
        `operator` - 'eq', 'gt', 'lt'
    """
    if request.method == 'POST':
        # Run the query
        response = keen.extraction('answers', filters=[request.form.to_dict()])
        if len(response) == 0:
            return 'No results found'

        # Display the response
    # Display the form


# Handlersfor testing styling.
def analysistest():
    return render_template('analysistest.haml')


def studenttestview():
    return render_template('studenttestview.haml')


def lecturertestview():
    return render_template('lecturertestview.haml')


def populate():
    admin = User.create('admin', 'password', 'admin')
    admin.put()
    user0 = User.create('hod', 'password', 'lecturer')
    hod = Lecturer(name='HOD', title='Dr', user=user0.key)
    hod.put()
    faculty = Faculty(name='Pure and Applied Science',
                      head_of_department=hod.key)
    faculty.put()
    department = Department(name='Computing', faculty=faculty.key)
    department.put()

    user1 = User.create('student', 'password', 'student')
    student = Student(name='Kevin Leyow', email_address='kleyow@gmail.com',
                      user=user1.key)

    user2 = User.create('lecturer', 'password', 'lecturer')
    lecturer = Lecturer(name='Jimmy', title='Dr',
                        user=user2.key, department=department.key)

    course = Course(name='Comp3800', total_students=30,
                    department=department.key,
                    faculty=faculty.key)
    course2 = Course(name='Comp2600', total_students=20,
                     department=department.key,
                     faculty=faculty.key)

    ndb.put_multi([lecturer, course])
    ndb.put_multi([lecturer, course2])

    class_ = Class(course=course.key, lecturer=lecturer.key)
    class2_ = Class(course=course2.key, lecturer=lecturer.key)
    class_.put()
    class2_.put()

    student.courses = [class_.key, class2_.key]
    lecturer.courses = [class_.key, class2_.key]
    ndb.put_multi([student, lecturer])

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


def warmup():
    """App Engine warmup handler
    """
    return ''
