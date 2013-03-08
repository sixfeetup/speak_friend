from unittest import TestCase


from pyramid import testing
from speak_friend.forms import profiles


class FormTests(TestCase):
    def test_profile_form_policy_title(self):
        req = testing.DummyRequest()
        self.assertEqual(profiles.make_profile_form(req)['agree_to_policy'].title,
                         'I agree to the usage policy.')

    def test_profile_form_email_fields(self):
        req = testing.DummyRequest()
        self.assertEqual(
            profiles.make_profile_form(req)['email'].widget.__class__.__name__,
            'CheckedInputWidget')

    def test_profile_form_password_fields(self):
        req = testing.DummyRequest()
        self.assertEqual(
            profiles.make_profile_form(req)['password'].widget.__class__.__name__,
            'StrengthValidatingPasswordWidget')
