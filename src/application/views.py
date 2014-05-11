import datetime
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
from application.forms import LoginForm, SignupForm
from application.models import Student, Lecturer, Course, Class, \
                               Answer, Question, StudentSurvey, Survey, User, \
                               Faculty, Department, School


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
    completed = []

    for course in courses:
        survey = StudentSurvey.query(
            ancestor=course.key).filter(
            StudentSurvey.participant == current_user.key).get()
        if survey is not None:
            courses.remove(course)
            completed.append(course)

    all_classes = Class.query()
    return render_template(
        'studenthome.haml', student=student, courses=courses,
        all_classes=all_classes, completed=completed)


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


def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User.create(form.username.data, form.password.data, 'student')
        student = Student(user=user.key, name=form.name.data,
                          email_address=form.email_address.data,
                          dob=datetime.datetime.strptime(form.dob.data, '%Y-%m-%d'),
                          status=form.status.data,
                          gender=form.gender.data, year=form.year.data)
        student.put()
        return redirect(url_for('login'))

    return render_template('signup.haml', form=form)


@login_required
def survey(course_key):
    try:
        course = ndb.Key(urlsafe=course_key).get()

    except db.BadKeyError:
        course = None

    if course is None:
        return abort(404)

    if request.method == 'POST':
        survey = StudentSurvey(
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
        deferred.defer(
            _send_to_keen, survey.key, course.key, [answer.key for answer in answers])
        return redirect(url_for('home'))

    questions = Question.get_active()
    return render_template(
        'survey.haml',
        questions=questions,
        course=course)


def _send_to_keen(survey_key, course_key, answer_keys):
    events = []
    student = Student.query(Student.user == survey_key.get().participant).get()
    course = course_key.get()
    answers = ndb.get_multi(answer_keys)
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
            'course': {
                'name': course.course.get().name,
                'department': course.course.get().department.get().name,
                'faculty': course.course.get().faculty.get().name,
            },
            'question_number': question.number,
            'lecturer': {
                'key': lecturer.key.urlsafe(),
                'name': lecturer.name,
                'department': lecturer.department.get().name,
                'faculty': lecturer.department.get().faculty.get().name,
            },
            'student': {
                'key': student.key.urlsafe(),
                'age': student.calculate_age(),
                'gender': student.gender,
                'status': student.status,
                'year': student.year,
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
    surveys = StudentSurvey.query(ancestor=class_.key)
    return render_template(
        'analysis.haml',
        surveys=surveys,
        course=course,
        lecturer=lecturer,
        class_key=class_key,
        questions=Question.get_active())


@login_required
def responses(class_key, question_key):
    answers = []

    try:
        class_ = ndb.Key(urlsafe=class_key).get()
        question = ndb.Key(urlsafe=question_key).get()

    except db.BadKeyError:
        class_ = None

    if class_ is None:
        return abort(404)

    surveys = StudentSurvey.query(ancestor=class_.key).fetch()

    for survey in surveys:
        answerss = Answer.query(Answer.question == question.key,
                                ancestor=survey.key).fetch()
        for answer in answerss:
            answers.append(str(answer.string_value))

    return render_template('responses.haml', answers=answers,
                           question=question)


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
        subject = 'Course Review StudentSurvey'
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
    import datetime
    admin = User.create('admin', 'password', 'admin')
    admin.put()

    principal_user = User.create('principal', 'password', 'lecturer')
    principal = Lecturer(name='Principal', title='Dr', user=principal_user.key)
    principal.put()

    school = School(name='University of The West Indies - Mona',
                    principal=principal.key)
    school.put()

    hof_user1 = User.create('hof1', 'password', 'lecturer')
    hof_user2 = User.create('hof2', 'password', 'lecturer')
    hof1 = Lecturer(name='Head Of Pure and Applied', title='Dr',
                    user=hof_user1.key)
    hof2 = Lecturer(name='Head Of Medical Sciences', title='Dr',
                    user=hof_user2.key)
    hof1.put()
    hof2.put()

    faculty1 = Faculty(name='Pure and Applied Science', school=school.key,
                       head_of_faculty=hof1.key)
    faculty2 = Faculty(name='Medical Sciences', school=school.key,
                       head_of_faculty=hof2.key)
    faculty1.put()
    faculty2.put()

    hod_user1 = User.create('hod1', 'password', 'lecturer')
    hod_user2 = User.create('hod2', 'password', 'lecturer')
    hod_user3 = User.create('hod3', 'password', 'lecturer')
    hod_user4 = User.create('hod4', 'password', 'lecturer')
    hod1 = Lecturer(name='Head Of Computing', title='Dr', user=hod_user1.key)
    hod2 = Lecturer(name='Head Of Mathematics', title='Dr', user=hod_user2.key)
    hod3 = Lecturer(name='Head Of Medicine', title='Dr', user=hod_user3.key)
    hod4 = Lecturer(name='Head Of Microbiology', title='Dr', user=hod_user4.key)
    hod1.put()
    hod2.put()
    hod3.put()
    hod4.put()

    department1 = Department(name='Computing', faculty=faculty1.key,
                             head_of_department=hod1.key)
    department2 = Department(name='Mathematics', faculty=faculty1.key,
                             head_of_department=hod2.key)
    department3 = Department(name='Medicine', faculty=faculty2.key,
                             head_of_department=hod3.key)
    department4 = Department(name='Microbiology', faculty=faculty2.key,
                             head_of_department=hod4.key)
    department1.put()
    department2.put()
    department3.put()
    department4.put()

    principal.department = department4.key
    hof1.department = department2.key
    hof2.department = department3.key
    hod1.department = department1.key
    hod2.department = department2.key
    hod3.department = department3.key
    hod4.department = department4.key
    principal.put()
    hof1.put()
    hof2.put()
    hod1.put()
    hod2.put()
    hod3.put()
    hod4.put()

    student_user = User.create('student', 'password', 'student')
    student = Student(name='Kevin Leyow', email_address='kleyow@gmail.com',
                      user=student_user.key, dob=datetime.date(year=1992, month=4, day=12),
                      year=3, status='FT', gender='M')

    lecturer_user = User.create('lecturer', 'password', 'lecturer')
    lecturer = Lecturer(name='Jimmy', title='Dr',
                        user=lecturer_user.key, department=department1.key)

    course = Course(name='Comp3161 - Database Management Systems',
                    total_students=90,
                    department=department1.key,
                    faculty=faculty1.key)
    course2 = Course(name='Comp3702 - Theory Of Computation',
                     total_students=20,
                     department=department1.key,
                     faculty=faculty1.key)

    ndb.put_multi([lecturer, course])
    ndb.put_multi([lecturer, course2])

    class_ = Class(course=course.key, lecturer=lecturer.key)
    class2_ = Class(course=course2.key, lecturer=lecturer.key)
    class_.put()
    class2_.put()

    student.courses = [class_.key, class2_.key]
    lecturer.courses = [class_.key, class2_.key]
    ndb.put_multi([student, lecturer])

    survey = Survey(
        title='General survey', description='A general survey')
    survey_key = survey.put()

    with open('application/questions.txt') as f:
        questions = []
        for number, line in enumerate(f.readlines()):
            question_type, dimension, question = line.split('|')
            questions.append(Question(question_type=question_type,
                                      dimension=dimension,
                                      question=question,
                                      is_active=True,
                                      number=number + 1,
                                      parent=survey_key))
    ndb.put_multi(questions)
    return 'Done.'


def warmup():
    """App Engine warmup handler
    """
    return ''
