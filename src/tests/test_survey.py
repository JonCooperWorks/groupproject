from lib import testing

from application.models import Question


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
