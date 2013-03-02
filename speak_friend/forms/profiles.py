import re
from pkg_resources import resource_filename

from colander import Bool, MappingSchema, SchemaNode, String, Integer, Invalid
from colander import Email, Regex
from deform import Button, Form
from deform import ZPTRendererFactory
from deform.widget import CheckedInputWidget
from deform.widget import CheckedPasswordWidget
from deform.widget import ResourceRegistry

from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile


# set a resource registry that contains resources for the password widget
password_registry = ResourceRegistry()
password_registry.set_js_resources('password', None,
                                   'js/zxcvbn-async.js',
                                   'js/password_strength.js')
password_registry.set_css_resources('password', None,
                                    'css/password_strength.css')


# set a template renderer that loads both deform and speak_friend templates
deform_path = resource_filename('deform', 'templates')
deform_bootstrap_path = resource_filename('deform_bootstrap', 'templates')
speak_friend_path = resource_filename('speak_friend', 'templates')
search_path = (speak_friend_path, deform_bootstrap_path, deform_path)
renderer = ZPTRendererFactory(search_path)


class StrengthValidatingPasswordWidget(CheckedPasswordWidget):
    requirements = (('jquery.maskedinput', None),
                    ('password', None), )
    template = 'widgets/strength_validating_password'


class Profile(MappingSchema):
    username = SchemaNode(String())
    first_name = SchemaNode(String())
    last_name = SchemaNode(String())
    email = SchemaNode(String(),
                       validator=Email(),
                       widget=CheckedInputWidget())
    password = SchemaNode(String(),
                          widget=StrengthValidatingPasswordWidget())
    agree_to_policy = SchemaNode(Bool(),
                                 title='I agree to the usage policy.')
    captcha = SchemaNode(String())


# instantiate our form with custom registry and renderer to get extra
# templates and resources
profile_form = Form(Profile(), buttons=('submit', 'cancel'),
                    resource_registry=password_registry,
                    renderer=renderer)


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


class PasswordResetRequest(MappingSchema):
      email = SchemaNode(
          String(),
          title=u'Email Address',
          validator=UserEmail(),
      )


password_reset_request_form = Form(
    PasswordResetRequest(),
    buttons=(
        Button('submit', title='Request Password'),
        'cancel'
    ),
)
