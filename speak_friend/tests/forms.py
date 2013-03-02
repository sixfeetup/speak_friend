from unittest import TestCase

from speak_friend.forms import profiles


class FormTests(TestCase):
    def test_profile_form_policy_title(self):
        self.assertEqual(profiles.profile_form['agree_to_policy'].title,
                         'I agree to the usage policy.')

    def test_profile_form_email_fields(self):
        self.assertEqual(
            profiles.profile_form['email'].widget.__class__.__name__,
            'CheckedInputWidget')

    def test_profile_form_password_fields(self):
        self.assertEqual(
            profiles.profile_form['password'].widget.__class__.__name__,
            'StrengthValidatingPasswordWidget')


