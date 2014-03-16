from lib import testing

from application.models import Question, Answer


class SurveyTestCase(testing.TestCase):

    def test_get_survey(self):
        Question(question='What do?', number=1, question_type='closed',
                 is_active=True).put()
        Question(question='Shouldn\'t show', number=2, question_type='closed',
                 is_active=False).put()
        response = self.app.get('/survey')
        self.assertEqual(200, response.status_code)
        self.assertTrue('What do?' in response.data)
        self.assertFalse('Shouldn\'t show' in response.data)

    def test_post_survey(self):
        question_key = Question(question='What do?', number=1, question_type='closed',
                                is_active=True).put()
        response = self.app.post('/survey', data={question_key.urlsafe(): 4})
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, Answer.query().count())
