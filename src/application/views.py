from flask import render_template, url_for, redirect
from flask_cache import Cache

from application import app
from application.forms import LoginForm
from application.models import User


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


def home():
    return redirect(url_for('login'))


def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user is None:
            return render_template('login.haml', error='Invalid login')

        return redirect(url_for('survey'))
    return render_template('login.haml')


def survey():
    return render_template('survey.haml')


def analysis():
    return render_template('analysis.haml')


def signup():
    return render_template('signup.haml')


# Handlersfor testing styling.
def surveytest():
    return render_template('surveytest.haml')


def analysistest():
    return render_template('analysistest.haml')


def warmup():
    """App Engine warmup handler
    """
    return ''
