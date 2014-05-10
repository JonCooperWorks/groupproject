"""
forms.py

Web forms based on Flask-WTForms

See: http://flask.pocoo.org/docs/patterns/wtforms/
     http://wtforms.simplecodes.com/

"""

from flaskext import wtf
from flaskext.wtf import validators


class LoginForm(wtf.Form):
    username = wtf.StringField(u'Username', validators=[validators.Required()])
    password = wtf.PasswordField(
        u'Password', validators=[validators.Required()])


class QuestionForm(wtf.Form):
    parent = wtf.StringField(validators=[validators.Required])
    question_type = wtf.StringField(choices=['open', 'closed', 'peer'],
                                    validators=[validators.Required])
    question = wtf.StringField(validators=[validators.Required])
    is_active = wtf.BooleanField(validators=[validators.Required])
    dimension = wtf.StringField(validators=[validators.Required])


class SurveyForm(wtf.Form):
    title = wtf.StringField(validators=[validators.Required])
    description = wtf.StringField(validators=[validators.Required])
    max_scale = wtf.IntegerField(choices=[3, 5, 7],
                                 validators=[validators.Required])
