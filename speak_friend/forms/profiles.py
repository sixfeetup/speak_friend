import re
from pkg_resources import resource_filename

from colander import Bool, MappingSchema, SchemaNode, String, Integer, Invalid
from colander import All, Email, Function, Regex, null, deferred
from deform import Button, Form
from deform import ZPTRendererFactory
from deform.widget import CheckedInputWidget
from deform.widget import CheckedPasswordWidget, PasswordWidget
from deform.widget import HiddenWidget
from deform.widget import ResourceRegistry
from deform.widget import TextInputWidget

from speak_friend.forms.recaptcha import deferred_recaptcha_widget
from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile
from speak_friend.models.profiles import DomainProfile


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


class UserEmail(object):
    """Validator to check email existence in UserProfiles

    If ``msg`` is supplied, it will be the error message to be used when
    raising `colander.Invalid`; otherwise, defaults to 'No user with that email address'

    The ``should_exist`` keyword argument specifies whether the validator checks for the
    email existing or not in the table. It defaults to `True`
    """
    def __init__(self, msg=None, should_exist=True, for_edit=False):
        if msg is None:
            msg = "No user with that email address"
        self.msg = msg
        self.should_exist = should_exist
        self.for_edit = for_edit

    def __call__(self, node, value):
        session = DBSession()
        # This relies on the current_value attribute being set
        # when the form is created (based on the authenticated username)
        if self.for_edit and value == node.current_value:
            return True
        query = session.query(UserProfile)
        query = query.filter(UserProfile.email==value)
        exists = bool(query.count())
        if exists != self.should_exist:
            raise Invalid(node, self.msg)


class DomainName(object):
    """Validator to check for exising domain names in DomainProfiles

    If ``msg`` is supplied, it will be the error message to be used when
    raising `colander.Invalid`; otherwise, defaults to 'A domain with that 
    name already exists'

    The ``should_exist`` keyword argument specifies whether the validator 
    checks for the domain name existing or not. It defaults to `False`
    """
    def __init__(self, msg=None, should_exist=False):
        if msg is None:
            msg = "A domain with that name already exists"
        self.msg = msg
        self.should_exist = should_exist

    def __call__(self, node, value):
        session = DBSession()
        query = session.query(DomainProfile)
        query = query.filter(DomainProfile.name==value)
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


def usage_policy_validator(value):
    return value == True


@deferred
def create_password_validator(node, kw):
    request = kw.get('request')
    ctx_validator = request.registry.password_validator

    def inner_password_validator(value):
        error_msg = ctx_validator(value)
        if not error_msg:
            return True
        else:
            return error_msg
    return Function(inner_password_validator)


class Profile(MappingSchema):
    username = SchemaNode(
        String(),
        validator=Function(username_validator(False)),
        description='* we suggest using your first and last name',
    )
    first_name = SchemaNode(String())
    last_name = SchemaNode(String())
    email = SchemaNode(
        String(),
        title=u'Email Address',
        validator=All(
            Email(),
            UserEmail(should_exist=False,
                      msg="Email address already in use."),
        ),
        widget=CheckedInputWidget(subject=u'Email Address',
                                  confirm_subject=u'Confirm Email Address'),
    )
    password = SchemaNode(
        String(),
        widget=StrengthValidatingPasswordWidget(),
        description='* Minimum of 8 characters and must include one non-alpha character.',
        validator=create_password_validator,
    )
    agree_to_policy = SchemaNode(
        Bool(),
        title='I agree to the site policy.',
        validator=Function(usage_policy_validator,
                           message='Agreement with the site policy is required.'),
    )
    captcha = SchemaNode(
        String(),
        widget=deferred_recaptcha_widget,
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


class EditProfileSchema(MappingSchema):
    username = SchemaNode(
        String(),
        missing='',
        widget=TextInputWidget(template='readonly/textinput'),
    )
    first_name = SchemaNode(String(),
                           required=False)
    last_name = SchemaNode(String(),
                          required=False)
    email = SchemaNode(
        String(),
        title=u'Email Address',
        validator=All(
            Email(),
            UserEmail(should_exist=False, for_edit=True,
                      msg="Email address already in use."),
        ),
        widget=CheckedInputWidget(subject=u'Email Address',
                                  confirm_subject=u'Confirm Email Address'),
    )
    password = SchemaNode(
        String(),
        required=False,
        missing=null,
        description=u"Password only required if changing email.",
        widget=PasswordWidget(),
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


# instantiate our form with custom registry and renderer to get extra
# templates and resources
def make_profile_form(request, edit=False):
    if edit:
        # We need to attach the current value of the user's email
        # so we know if they're trying to change it during validation
        schema = EditProfileSchema()
        for fld in schema:
            if fld.name == 'email':
                fld.current_value = request.user.email
    else:
        schema = Profile().bind(request=request)
    form = Form(
        schema,
        buttons=('submit', 'cancel'),
        resource_registry=password_registry,
        renderer=renderer,
        bootstrap_form_style='form-vertical',
    )
    return form


class Domain(MappingSchema):
    name = SchemaNode(
        String(),
        title="Domain Name",
        description="Must be a valid Fully Qualified Domain Name",
        validator=All(FQDN(), DomainName(), ),
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
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


def make_password_reset_request_form(request=None):
    password_reset_request_form = Form(
        PasswordResetRequest(),
        bootstrap_form_style='form-vertical',
        buttons=(
            Button('submit', title='Request Password'),
            'cancel'
        ),
    )
    return password_reset_request_form


class Login(MappingSchema):
    login = SchemaNode(
        String(),
        title='Username or Email',
    )
    password = SchemaNode(
        String(),
        widget=PasswordWidget(),
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


def make_login_form(action=''):
    login_form = Form(
        Login(),
        action=action,
        bootstrap_form_style='form-vertical',
        buttons=(
            Button('submit', title='Log In'),
            'cancel'
        )
    )
    return login_form


class PasswordReset(MappingSchema):
    password = SchemaNode(
        String(),
        widget=StrengthValidatingPasswordWidget(),
        validator=create_password_validator
    )


def make_password_reset_form(request=None):
    schema = PasswordReset()
    if request:
        schema = PasswordReset().bind(request=request)
    password_reset_form = Form(
        schema,
        bootstrap_form_style='form-vertical',
        buttons=(
            Button('submit', title='Reset Password'),
            'cancel'
        ),
        resource_registry=password_registry,
        renderer=renderer
    )
    return password_reset_form


class PasswordChange(MappingSchema):
    password = SchemaNode(
        String(),
        widget=PasswordWidget(),
    )
    new_password = SchemaNode(
        String(),
        missing=null,
        widget=StrengthValidatingPasswordWidget(),
        description='* Minimum of 8 characters and must include one non-alpha character.',
        validator=create_password_validator
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


def make_password_change_form(request=None):
    schema = PasswordChange()
    if request:
        schema = PasswordChange().bind(request=request)
    password_reset_form = Form(
        schema,
        bootstrap_form_style='form-vertical',
        buttons=(
            Button('submit', title='Change Password'),
            'cancel'
        ),
        resource_registry=password_registry,
        renderer=renderer
    )
    return password_reset_form
