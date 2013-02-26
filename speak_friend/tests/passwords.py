import os

import ConfigParser
from unittest import TestCase


# from speak_friend.passwords import check_password
# from speak_friend.passwords import make_disallowed_regex
# from speak_friend.passwords import get_chartype_counts
# from speak_friend.passwords import password_settings
# from speak_friend.passwords import DEFAULT_PASSWORD_SETTINGS
from speak_friend.passwords import PASSWORD_SETTINGS_PREFIX
from speak_friend.passwords import PasswordValidator
# from speak_friend.passwords import ERROR_MESSAGES
from speak_friend.tests.common import SFBaseCase


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INI_FILE_PATH = os.path.join(CURRENT_DIR, 'resources', 'test_password.ini')
PASSWORD_CONFIG = ConfigParser.ConfigParser()
PASSWORD_CONFIG.read(INI_FILE_PATH)


class PasswordToolsTests(TestCase):
    def setUp(self):
        # self.settings = DEFAULT_PASSWORD_SETTINGS.copy()
        self.validator = PasswordValidator()
        self.passwords = {
            'alpha_lower': ['abcdef', [6,0,0,0]],
            'alpha_upper': ['ABCDEF', [0,6,0,0]],
            'alpha_mixed': ['abcDEF', [3,3,0,0]],
            'numeric': ['123456',[0,0,6,0]],
            'alphanumeric_lower': ['123abc', [3,0,3,0]],
            'alphanumeric_upper': ['123ABC', [0,3,3,0]],
            'alphanumeric_mixed': ['12aAbB', [2,2,2,0]],
            'special': ['!#@{%^', [0,0,0,6]],
            'complex': ['yRo8$D', [2,2,1,1]],
            'long_complex': ['nYfJ6UUt$8y4j+]W', [5,5,3,3]]
        }

    def decompose_charcounts(self, password):
        """return counts for character types in uniform order

        will always return the count as lower, upper, numeric, special
        """
        out = []
        counts = self.validator._get_chartype_counts(password)
        for key in ['min_lower', 'min_upper', 'min_numeric', 'min_special']:
            out.append(counts[key])
        return out

    def test_get_chartype_counts(self):
        """characters in a password can be correctly categorized"""
        for key, val in self.passwords.items():
            password, expected = val
            actual = self.decompose_charcounts(password)
            err_msg = "char count for %s incorrect: expected %s but got %s"
            self.assertEqual(expected, actual, 
                             err_msg % (key, expected, actual))

    def test_disallowed_reg(self):
        """a constructed regular expression correctly finds matches
        """
        for disallowed, keymatch in [('abcABC', 'alpha'),
                                     ('123', 'numeric'),
                                     ('$+]', 'complex')]:
            regex = self.validator._make_disallowed_regex(disallowed)
            for key, val in self.passwords.items():
                password = val[0]
                found = bool(len(regex.findall(password)))
                if keymatch in key:
                    self.assertTrue(found)
                else:
                    self.assertFalse(found)

    def test_password_okay_permissive(self):
        """default settings allow any password to pass"""
        for key, val in self.passwords.items():
            password = val[0]
            self.assertEqual(self.validator(password), None)

    def test_password_min_length(self):
        testkey = 'min_length'
        key = '.'.join([PASSWORD_SETTINGS_PREFIX, testkey])
        validator = PasswordValidator({key: 7})
        expected_error = validator._get_error_message(testkey)
        for key, val in self.passwords.items():
            password = val[0]
            result = validator(password)
            if 'long' in key:
                self.assertEqual(result, None)
            else:
                self.assertTrue(result is not None)
                self.assertEqual(result, expected_error)

    def test_password_max_length(self):
        testkey = 'max_length'
        key = '.'.join([PASSWORD_SETTINGS_PREFIX, testkey])
        validator = PasswordValidator({key: 7})
        expected_error = validator._get_error_message(testkey)
        for key, val in self.passwords.items():
            password = val[0]
            result = validator(password)
            if 'long' not in key:
                self.assertEqual(result, None)
            else:
                self.assertTrue(result is not None)
                self.assertEqual(result, expected_error)

    def test_password_min_lower(self):
        testkey = 'min_lower'
        key = '.'.join([PASSWORD_SETTINGS_PREFIX, testkey])
        validator = PasswordValidator({key: 5})
        expected_error = validator._get_error_message(testkey)
        for key, val in self.passwords.items():
            password = val[0]
            result = validator(password)
            if 'alpha_lower' in key or 'long_complex' in key:
                self.assertEqual(result, None)
            else:
                self.assertTrue(result is not None)
                self.assertEqual(result, expected_error)

    def test_password_min_upper(self):
        testkey = 'min_upper'
        key = '.'.join([PASSWORD_SETTINGS_PREFIX, testkey])
        validator = PasswordValidator({key: 5})
        expected_error = validator._get_error_message(testkey)
        for key, val in self.passwords.items():
            password = val[0]
            result = validator(password)
            if 'alpha_upper' in key or 'long_complex' in key:
                self.assertEqual(result, None)
            else:
                self.assertTrue(result is not None)
                self.assertEqual(result, expected_error)

    def test_password_min_numeric(self):
        testkey = 'min_numeric'
        key = '.'.join([PASSWORD_SETTINGS_PREFIX, testkey])
        validator = PasswordValidator({key: 2})
        expected_error = validator._get_error_message(testkey)
        for key, val in self.passwords.items():
            password = val[0]
            result = validator(password)
            if 'numeric' in key or 'long_complex' in key:
                self.assertEqual(result, None)
            else:
                self.assertTrue(result is not None)
                self.assertEqual(result, expected_error)

    def test_password_min_special(self):
        testkey = 'min_special'
        key = '.'.join([PASSWORD_SETTINGS_PREFIX, testkey])
        validator = PasswordValidator({key: 3})
        expected_error = validator._get_error_message(testkey)
        for key, val in self.passwords.items():
            password = val[0]
            result = validator(password)
            if key in ['special', 'long_complex']:
                self.assertEqual(result, None)
            else:
                self.assertTrue(result is not None)
                self.assertEqual(result, expected_error)

    def test_password_disallowed(self):
        testkey = 'disallowed'
        key = '.'.join([PASSWORD_SETTINGS_PREFIX, testkey])
        validator = PasswordValidator({key: '$+]'})
        expected_error = validator._get_error_message(testkey)
        for key, val in self.passwords.items():
            password = val[0]
            result = validator(password)
            if 'complex' not in key:
                self.assertEqual(result, None)
            else:
                self.assertTrue(result is not None)
                self.assertEqual(result, expected_error)

    def test_password_multiple_errors(self):
        keys = ['min_lower', 'min_upper', 'min_numeric', 'min_special']
        keys = map(lambda x: '.'.join([PASSWORD_SETTINGS_PREFIX, x]), keys)
        expected_error_keys = ['min_numeric', 'min_special', 'min_length']
        settings = dict([(key, 2) for key in keys])
        settings['.'.join([PASSWORD_SETTINGS_PREFIX, 'min_length'])] = 8
        validator = PasswordValidator(settings)
        for pwkey in ['complex', 'long_complex']:
            password = self.passwords[pwkey][0]
            result = validator(password)
            if 'long' in pwkey:
                self.assertEqual(result, None)
            else:
                msg = "%s passed but should not have"
                self.assertTrue(result is not None, msg % pwkey)
                for errkey in expected_error_keys:
                    errmsg = validator._get_error_message(errkey)
                    self.assertTrue(errmsg in result, 'missing "%s"' % errmsg)
# 
# 
# class PasswordSettingsTests(SFBaseCase):
#     """verify that integrating with actual settings works correctly"""
#     def setUp(self):
#         super(PasswordSettingsTests, self).setUp()
#         self.prefix = PASSWORD_SETTINGS_PREFIX
#         self.use_settings = {
#             'min_length': (10, int),
#             'max_length': (10, int),
#             'min_lower': (10, int),
#             'min_upper': (10, int),
#             'min_numeric': (10, int),
#             'min_special': (10, int),
#             'disallowed': ("$#!%&{'[\"}])(", str)
#         }
# 
#     def test_set_integer_vals(self):
#         for key in ['min_length', 'max_length', 'min_lower', 'min_upper',
#                     'min_numeric', 'min_special']:
#             regkey = '.'.join([self.prefix, key])
#             expected, expected_type = self.use_settings[key]
#             self.config.add_settings(
#                 dict(PASSWORD_CONFIG.items(key)))
#             settings = password_settings()
#             actual = settings[key]
#             self.assertEqual(expected, actual)
#             self.assertTrue(isinstance(actual, expected_type))
# 
#     def test_set_string_val(self):
#         key = 'disallowed'
#         expected, expected_type = self.use_settings[key]
#         self.config.add_settings(
#             dict(PASSWORD_CONFIG.items(key)))
#         settings = password_settings()
#         actual = settings[key]
#         self.assertEqual(expected, actual)
#         self.assertTrue(isinstance(actual, expected_type))
# 
#     def test_set_all_vals(self):
#         confkey = 'multiple'
#         self.config.add_settings(
#             dict(PASSWORD_CONFIG.items(confkey)))
#         for key in DEFAULT_PASSWORD_SETTINGS.keys():
#             expected, expected_type = self.use_settings[key]
#             settings = password_settings()
#             actual = settings[key]
#             self.assertEqual(expected, actual)
#             self.assertTrue(isinstance(actual, expected_type))
# 
#     def test_set_nonevals(self):
#         """what happens when the value in .ini is nothing
#         """
#         confkey = 'nonevals'
#         self.config.add_settings(
#             dict(PASSWORD_CONFIG.items(confkey)))
#         for key in DEFAULT_PASSWORD_SETTINGS.keys():
#             expected_type = self.use_settings[key][1]
#             expected = DEFAULT_PASSWORD_SETTINGS[key]
#             settings = password_settings()
#             actual = settings[key]
#             self.assertEqual(expected, actual, 'bad value for %s' % key)
