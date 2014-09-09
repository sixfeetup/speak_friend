from speak_friend.forms import profiles
from speak_friend.tests.common import SFBaseCase


class FormTests(SFBaseCase):
    def test_profile_form_policy_title(self):
        self.request.user = None
        self.assertEqual(
            profiles.make_profile_form(self.request)['agree_to_policy'].title,
            'I agree to the site policy.')

    def test_profile_form_email_fields(self):
        form = profiles.make_profile_form(self.request)
        self.assertEqual(
            form['email'].widget.__class__.__name__,
            'CheckedInputWidget')

    def test_profile_form_password_fields(self):
        form = profiles.make_profile_form(self.request)
        self.assertEqual(
            form['password'].widget.__class__.__name__,
            'StrengthValidatingPasswordWidget')
