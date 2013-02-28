import re

from colander import Bool, MappingSchema, SchemaNode, String, Integer, Invalid
from colander import Email, Regex
from deform import Form
from deform.widget import CheckedInputWidget, CheckedPasswordWidget

from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile


class Profile(MappingSchema):
    username = SchemaNode(String())
    first_name = SchemaNode(String())
    last_name = SchemaNode(String())
    email = SchemaNode(String(),
                       validator=Email(),
                       widget=CheckedInputWidget())
    password = SchemaNode(String(),
                          widget=CheckedPasswordWidget())
    agree_to_policy = SchemaNode(Bool(),
                                 title='I agree to the usage policy.')
    captcha = SchemaNode(String())


profile_form = Form(Profile(), buttons=('submit', 'cancel'))


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
    """Validator to ensure an email exists in UserProfiles

    If ``msg`` is supplied, it will be the error message to be used when
    raising `colander.Invalid`; otherwise, defaults to 'No user with that email address'
    """
    def __init__(self, msg=None):
        if msg is None:
            msg = "No user with that email address"
        super(UserEmail, self).__init__(msg=msg)

    def __call__(self, node, value):
        super(UserEmail, self).__call__(node, value)
        session = DBSession()
        query = session.query(UserProfile)
        query = query.filter(UserProfile.email==value)
        results = query.count()
        if results == 0:
            raise Invalid(node, self.msg)


class Domain(MappingSchema):
    name = SchemaNode(
        String(),
        title="Domain Name",
        description="Must be a valid Fully Qualified Domain Name",
        validator=FQDN())
    password_valid = SchemaNode(
        Integer(),
        title="Password valid",
        description="Indicate the length of time, in minutes that a password "
                    "should be valid (a negative value will use the system "
                    "default)")
    max_attempts = SchemaNode(
        Integer(),
        title="Maximum login attempts",
        description="Indicate the number of times a user may fail a login "
                    "attempt before being disabled (a negative value will "
                    "use the system default)")
