from lib import testing
from application.models import User


class LoginTestCase(testing.TestCase):

    CREDENTIALS = ('username', 'password')

    def test_login_with_valid_credentials(self):
        User.create(*self.CREDENTIALS)
        username, password = self.CREDENTIALS
        response = self.app.post(
            '/login', data={'username': username, 'password': password})
        self.assertEqual(302, response.status_code)

    def test_login_with_invalid_credentials(self):
        User.create(*self.CREDENTIALS)
        username, password = self.CREDENTIALS
        response = self.app.post(
            '/login', data={'username': username, 'password': 'wrong'})
        self.assertEqual(200, response.status_code)
        self.assertIn('Invalid login', response.data)
