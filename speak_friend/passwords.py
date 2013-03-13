"""validation tools for passwords
"""
import re


UPPERS = re.compile(r'[A-Z]{1}')
LOWERS = re.compile(r'[a-z]{1}')
NUMBERS = re.compile(r'[0-9]{1}')
SPECIALS = re.compile(r'[\W|_]')
NON_ALPHA = re.compile(r'[^a-zA-Z]{1}')
PASSWORD_SETTINGS_PREFIX = 'speak_friend.password'


class PasswordValidator(object):
    default_settings = {
        'min_length': None,
        'max_length': None,
        'min_lower': 0,
        'min_upper': 0,
        'min_numeric': 0,
        'min_special': 0,
        'min_non_alpha': 0,
        'disallowed': None,
    }
    value_types = {
        'min_length': (int, None),
        'max_length': (int, None),
        'min_lower': (int, 0),
        'min_upper': (int, 0),
        'min_numeric': (int, 0),
        'min_special': (int, 0),
        'min_non_alpha': (int, 0),
        'disallowed': (None, None),
    }
    error_messages = {
        'min_length': 'Password must be at least %(min_length)d characters.',
        'max_length': 'Password must be shorter than %(max_length)d characters.',
        'min_lower': 'Password must contain at least %(min_lower)d lower case letters.',
        'min_upper': 'Password must contain at least %(min_upper)d upper case letters.',
        'min_numeric': 'Password must contain at least %(min_numeric)d numbers.',
        'min_special': 'Password must contain at least %(min_special)d special characters.',
        'min_non_alpha': 'Password must contain at least %(min_non_alpha)d non alphabetical characters.',
        'disallowed': 'Password may not contain the characters %(disallowed)s.'
    }
    disallowed = None

    def __init__(self, settings={}):
        calculated_settings = self.default_settings.copy()
        for key in self.default_settings.keys():
            regkey = '.'.join([PASSWORD_SETTINGS_PREFIX, key])
            if regkey in settings:
                # convert the incoming string to the appropriate type, with 
                # fallback supplied in case of inappropriate values from ini
                # 
                # XXX: Since we are doing this at system init time now, would
                # it be better to raise a ConfigurationError instead of 
                # defaulting?
                converter, fallback = self.value_types[key]
                value = settings[regkey]
                if converter is not None:
                    try:
                        value = converter(value)
                    except ValueError:
                        value = fallback
                else:
                    if not value:
                        value = fallback
                calculated_settings[key] = value

        self.settings = calculated_settings
        if self.settings['disallowed'] is not None:
            self.disallowed = self._make_disallowed_regex(
                self.settings['disallowed'])


    def __call__(self, password):
        """check given password against configured settings

        if any setting fails return error message, else return None
        """
        error_messages = []
        if self.settings['min_length'] is not None:
            if len(password) < self.settings['min_length']:
                error_messages.append(
                    self._get_error_message('min_length'))
        if self.settings['max_length'] is not None:
            if len(password) > self.settings['max_length']:
                error_messages.append(
                    self._get_error_message('max_length'))
        if self.disallowed is not None:
            if self.disallowed.search(password):
                error_messages.append(
                    self._get_error_message('disallowed'))
        counts = self._get_chartype_counts(password)
        for key, value in counts.items():
            if value < self.settings[key]:
                error_messages.append(self._get_error_message(key))
        if error_messages:
            return " ".join(error_messages) % self.settings

        return None

    def _get_chartype_counts(self, password):
        counts = {}
        counts['min_upper'] = len(UPPERS.findall(password))
        counts['min_lower'] = len(LOWERS.findall(password))
        counts['min_numeric'] = len(NUMBERS.findall(password))
        counts['min_special'] = len(SPECIALS.findall(password))
        counts['min_non_alpha'] = len(NON_ALPHA.findall(password))

        return counts

    def _make_disallowed_regex(self, disallowed):
        core = '[%s]{1}'
        pattern = core % '|'.join(map(re.escape, list(disallowed)))
        return re.compile(pattern)

    def _get_error_message(self, key):
        return self.error_messages[key] % self.settings
