"""
urls.py

URL dispatch route mappings and error handlers

"""
from flask import render_template

from application import app
from application import views


# URL dispatch rules
# App Engine warm up handler
app.add_url_rule('/_ah/warmup', 'warmup', view_func=views.warmup)

# Home page
app.add_url_rule('/', 'home', view_func=views.home)

# Login Page
app.add_url_rule(
    '/login', 'login', view_func=views.login, methods=['GET', 'POST'])

# Survey Page
app.add_url_rule('/survey', 'survey',  methods=['GET', 'POST'],
                 view_func=views.survey)

# Analysis Page
app.add_url_rule('/analysis', 'analysis', view_func=views.analysis)

# Signup Page
app.add_url_rule('/signup', 'signup', view_func=views.signup)

# Landing Page
app.add_url_rule('/landing', 'landing', view_func=views.landing)

# Mailer endpoint
app.add_url_rule('/notify-students', 'notify-students',
                 view_func=views.notify_students)

# Test route page allows me to style while work is done on the backend
app.add_url_rule('/surveytest', 'surveytest', view_func=views.surveytest)
app.add_url_rule('/analysistest', 'analysistest', view_func=views.analysistest)
app.add_url_rule('/studenttestview', 'studenttestview',
                 view_func=views.studenttestview)
app.add_url_rule('/lecturertestview', 'lecturertestview',
                 view_func=views.lecturertestview)


# Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
