from lib import testing
from application.models import Student


class MailerTestCase(testing.TestCase):

    def test_mails_are_sent(self):
        student = Student(email_address='test@example.org')
        student.put()
        response = self.app.get('/notify-students')
        self.assertEqual(200, response.status_code)
        messages = self.mail_stub.get_sent_messages()
        self.assertEqual(1, len(messages))
        message, = messages
        self.assertEqual(student.email_address, message.to)
