import re

from colander import Bool, MappingSchema, SchemaNode, String, Integer, Invalid
from colander import Email, Function, Regex
from deform import Button, Form
from deform.widget import CheckedInputWidget, CheckedPasswordWidget

from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile




fqdn_re = re.compile(
    r'(?=^.{1,254}$)(^(?:(?!\d+\.)[a-zA-Z0-9_\-]{1,63}\.?)+(?:[a-zA-Z]{2,})$)')


class FQDN(Regex):
    """Validator for a Fully Qualified Domain Name

    If ``msg`` is supplied, it will be the error message to be used when
    raising `colander.Invalid`; otherwise, defaults to 'Invalid domain name'
    """
    def __init__(self, msg=None):
        if msg is None:
            msg = "Invalid domain name"
        super(FQDN, self).__init__(fqdn_re, msg=msg)


class UserEmail(Email):
    """Validator to check email existence in UserProfiles

    If ``msg`` is supplied, it will be the error message to be used when
    raising `colander.Invalid`; otherwise, defaults to 'No user with that email address'

    The ``should_exist`` keyword argument specifies whether the validator checks for the
    email existing or not in the table. It defaults to `True`
    """
    def __init__(self, msg=None, should_exist=True):
        if msg is None:
            msg = "No user with that email address"
        self.should_exist = should_exist
        super(UserEmail, self).__init__(msg=msg)

    def __call__(self, node, value):
        super(UserEmail, self).__call__(node, value)
        session = DBSession()
        query = session.query(UserProfile)
        query = query.filter(UserProfile.email==value)
        exists = bool(query.count())
        if exists != self.should_exist:
            raise Invalid(node, self.msg)


def username_validator(should_exist):
    """Generates validator function to check existence of a username

    This function generates another function that will be used by a
    ``colander.Function`` validator.

    The ``should_exist`` argument specifies whether the validator
    checks for the user existing or not in the table. It defaults to `True`
    """
    def inner_username_validator(value):
        session = DBSession()
        query = session.query(UserProfile)
        query = query.filter(UserProfile.username==value)
        exists = bool(query.count())
        if exists != should_exist:
            if should_exist == True:
                return "Username does not exist."
            else:
                return "Username already exists."
        # Functions used with the function validator must return True.
        return True
    return inner_username_validator


class Profile(MappingSchema):
    username = SchemaNode(
        String(),
        validator=Function(username_validator(False)),
    )
    first_name = SchemaNode(String())
    last_name = SchemaNode(String())
    email = SchemaNode(
        String(),
        title=u'Email Address',
        validator=UserEmail(should_exist=False,
                         msg="Email address already in use."),
        widget=CheckedInputWidget(subject=u'Email Address',
                                 confirm_subject=u'Confirm Email Address'),
    )
    password = SchemaNode(
        String(),
        widget=CheckedPasswordWidget(),
    )
    agree_to_policy = SchemaNode(
        Bool(),
        title='I agree to the usage policy.',
    )
    captcha = SchemaNode(String())

profile_form = Form(Profile(), buttons=('submit', 'cancel'))


class Domain(MappingSchema):
    name = SchemaNode(
        String(),
        title="Domain Name",
        description="Must be a valid Fully Qualified Domain Name",
        validator=FQDN(),
    )
    password_valid = SchemaNode(
        Integer(),
        title="Password valid",
        description="Indicate the length of time, in minutes that a password "
                    "should be valid (a negative value will use the system "
                    "default)",
    )
    max_attempts = SchemaNode(
        Integer(),
        title="Maximum login attempts",
        description="Indicate the number of times a user may fail a login "
                    "attempt before being disabled (a negative value will "
                    "use the system default)",
    )


class PasswordResetRequest(MappingSchema):
      email = SchemaNode(
          String(),
          title=u'Email Address',
          validator=UserEmail(should_exist=True),
      )


password_reset_request_form = Form(
    PasswordResetRequest(),
    buttons=(
        Button('submit', title='Request Password'),
        'cancel'
    ),
)
