"""validation tools for passwords
"""
import re

# from pyramid.threadlocal import get_current_registry


UPPERS = re.compile(r'[A-Z]{1}')
LOWERS = re.compile(r'[a-z]{1}')
NUMBERS = re.compile(r'[0-9]{1}')
SPECIALS = re.compile(r'[\W|_]')
DEFAULT_PASSWORD_SETTINGS = {
    'min_length': None,
    'max_length': None,
    'min_lower': 0,
    'min_upper': 0,
    'min_numeric': 0,
    'min_special': 0,
    'disallowed': None, 
}
ERROR_MESSAGES = {
    'min_length': 'Password must be longer than %(min_length)d characters.',
    'max_length': 'Password must be shorter than %(max_length)d characters.',
    'min_lower': 'Password must contain at least %(min_lower)d lower case letters.',
    'min_upper': 'Password must contain at least %(min_upper)d upper case letters.',
    'min_numeric': 'Passowrd must contain at least %(min_numeric)d numbers.',
    'min_special': 'Password must contain at least %(min_special)d special characters.',
    'disallowed': 'Password may not contain the characters %(disallowed)s.'
}


# def password_settings():
#     settings = DEFAULT_PASSWORD_SETTINGS.copy
#     reg = get_current_registry()
#     for key in settings.keys():
#         if key in reg.settings:
#             settings[key] = reg.settings[key]
#     return settings


def get_chartype_counts(password):
    counts = {}
    counts['min_upper'] = len(UPPERS.findall(password))
    counts['min_lower'] = len(LOWERS.findall(password))
    counts['min_numeric'] = len(NUMBERS.findall(password))
    counts['min_special']  = len(SPECIALS.findall(password))

    return counts


def make_disallowed_regex(disallowed):
    core = '[%s]{1}'
    pattern = core % '|'.join(map(re.escape, list(disallowed)))
    return re.compile(pattern)


def check_password(password, settings):
    """check given password against configured settings

    if any setting fails return error message, else return None
    """
    error_messages = []
    if settings['min_length'] is not None:
        if len(password) < settings['min_length']:
            error_messages.append(ERROR_MESSAGES['min_length'])
    if settings['max_length'] is not None:
        if len(password) > settings['max_length']:
            error_messages.append(ERROR_MESSAGES['max_length'])
    if settings['disallowed'] is not None:
        pattern = make_disallowed_regex(settings['disallowed'])
        if pattern.search(password):
            error_messages.append(ERROR_MESSAGES['disallowed'])
    counts = get_chartype_counts(password)
    for key, value in counts.items():
        if value < settings[key]:
            error_messages.append(ERROR_MESSAGES[key])
    if error_messages:
        return " ".join(error_messages) % settings

    return None
