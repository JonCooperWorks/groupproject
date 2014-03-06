from flask import render_template, url_for, redirect
from flask_cache import Cache

from application import app


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


def home():
    return redirect(url_for('login'))


def login():
    return render_template('login.haml')


def survey():
    return render_template('survey.haml')


def analysis():
    return render_template('analysis.haml')


def signup():
    return render_template('signup.haml')

def landing():
    return render_template('landing.haml')


# Handlersfor testing styling.
def surveytest():
    return render_template('surveytest.haml')


def analysistest():
    return render_template('analysistest.haml')


def warmup():
    """App Engine warmup handler
    """
    return ''
