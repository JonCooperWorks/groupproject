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


class SignupForm(wtf.Form):
    username = wtf.StringField(u'Username', validators=[validators.Required()])
    password = wtf.PasswordField(
        u'Password', validators=[validators.Required()])
    email_address = wtf.StringField(u'Email', validators=[validators.Required()])
    name = wtf.StringField(u'Name', validators=[validators.Required()])
    dob = wtf.StringField(u'Date of Birth', validators=[validators.Required()])
    gender = wtf.StringField(u'Gender',
                             validators=[validators.AnyOf('M', 'F')])
    status = wtf.StringField(u'Status',
                             validators=[validators.AnyOf('FT', 'PT')])
    year = wtf.IntegerField(u'Year',
                            validators=[validators.Required()])
