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

# Logout
app.add_url_rule(
    '/logout', 'logout', view_func=views.logout)

# Survey Page
app.add_url_rule('/survey/<course_key>', 'survey',
                 methods=['GET', 'POST'],
                 view_func=views.survey)

# Analysis Page
app.add_url_rule('/analysis/<class_key>', 'analysis', view_func=views.analysis)

# Peer Review Page
app.add_url_rule('/peerreview', 'peerreview', view_func=views.peerreview)

# Signup Page
app.add_url_rule('/signup', 'signup', view_func=views.signup,
                 methods=['GET', 'POST'])

# Department overview Page
app.add_url_rule('/department/<department_key>', 'department_overview',
                 view_func=views.department_overview)

# Faculty overview Page
app.add_url_rule('/faculty/<faculty_key>', 'faculty_overview',
                 view_func=views.faculty_overview)

# Faculty overview Page
app.add_url_rule('/school/<school_key>', 'school_overview',
                 view_func=views.school_overview)

# Mailer endpoint
app.add_url_rule('/notify-students', 'notify-students',
                 view_func=views.notify_students)

# Custom queries
app.add_url_rule(
    '/query', 'query', methods=['GET', 'POST'], view_func=views.query)

# Test route pages
app.add_url_rule('/populate', 'populate', view_func=views.populate)

# Responses page
app.add_url_rule('/responses/<class_key>/<question_key>',
                 'responses', view_func=views.responses)

# Add lecturer
app.add_url_rule('/admin/add-lecturer', 'add_lecturer',
                 view_func=views.add_lecturer, methods=['GET', 'POST'])

# Add question
app.add_url_rule('/admin/add-question', 'add_question',
                 view_func=views.add_question, methods=['GET', 'POST'])

# Add survey
app.add_url_rule('/admin/add-survey', 'add_survey',
                 view_func=views.add_survey, methods=['GET', 'POST'])

# Validate password
app.add_url_rule('/validate',
                 view_func=views.validate, methods=['GET', 'POST'])

# Assign lecturer
app.add_url_rule('/admin/assign-lecturer', methods=['GET', 'POST'],
                 view_func=views.assign_lecturer)


# Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
