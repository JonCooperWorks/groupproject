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


class AddLecturerForm(wtf.Form):
    email_address = wtf.StringField(
        u'Email Address', validators=[validators.Required()])
    username = wtf.StringField(
        u'ID Number', validators=[validators.Required()])
    name = wtf.StringField(
        u'Name', validators=[validators.Required()])
    title = wtf.StringField(
        u'Title', validators=[validators.AnyOf(('Dr', 'Mr', 'Prof', 'Mrs', 'Ms'))])
    department = wtf.StringField(
        u'Department', validators=[validators.Required()])


class AddQuestionForm(wtf.Form):
    survey = wtf.StringField(
        u'Add to Survey', validators=[validators.Required()])
    question_type = wtf.StringField(
        u'Question Type', validators=[validators.AnyOf(('open', 'closed', 'peer'))])
    is_active = wtf.BooleanField(
        u'Active', validators=[validators.Required()])
    question = wtf.StringField(
        u'Question', validators=[validators.Required()])
    dimension = wtf.StringField(
        u'Dimension', validators=[validators.Required()])


class AddSurveyForm(wtf.Form):
    title = wtf.StringField(
        u'Title', validators=[validators.Required()])
    desc = wtf.StringField(
        u'Description', validators=[validators.Required()])
    max_scale = wtf.IntegerField(
        u'Scale', validators=[validators.Required()])
