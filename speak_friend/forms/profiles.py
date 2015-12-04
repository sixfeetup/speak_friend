import re
from pkg_resources import resource_filename

from colander import Bool, MappingSchema, SchemaNode, String, Integer, Invalid
from colander import All, Email, Function, null, deferred, Regex
from deform import Button, Form
from deform import ZPTRendererFactory
from deform.widget import CheckedInputWidget
from deform.widget import CheckedPasswordWidget, PasswordWidget
from deform.widget import HiddenWidget
from deform.widget import ResourceRegistry
from deform.widget import TextInputWidget

from sixfeetup.bowab.forms.widgets import CSRFSchema
from sixfeetup.bowab.forms.widgets import deferred_recaptcha_widget
from sixfeetup.bowab.forms.widgets import build_color_widget
from sixfeetup.bowab.forms.widgets import colorpicker_registry

from speak_friend.api import DEFAULT_PRIMARY_COLOR
from speak_friend.api import DEFAULT_SECONDARY_COLOR
from speak_friend.models.profiles import UserProfile
from speak_friend.models.profiles import DomainProfile


# set a resource registry that contains resources for the password widget
password_registry = ResourceRegistry()
password_registry.set_js_resources(
    'password', None,
    'speak_friend:static/js/zxcvbn-async.js',
    'speak_friend:static/js/password_strength.js')
password_registry.set_css_resources(
    'password', None, 'speak_friend:static/css/password_strength.css')


# set a template renderer that loads both deform and speak_friend templates
deform_path = resource_filename('deform', 'templates')
speak_friend_path = resource_filename('speak_friend', 'templates')
search_path = (speak_friend_path, deform_path)
renderer = ZPTRendererFactory(search_path)


class StrengthValidatingPasswordWidget(CheckedPasswordWidget):
    requirements = (('jquery.maskedinput', None),
                    ('password', None), )
    template = 'widgets/strength_validating_password'


# we need to create two separate deferred widgets, one for each color in the
# domain profile.
@deferred
def deferred_primary_color_widget(node, kw):
    color = kw['primary_color']
    default = kw['default_primary_color']
    return build_color_widget(color, default)


@deferred
def deferred_secondary_color_widget(node, kw):
    color = kw['secondary_color']
    default = kw['default_secondary_color']
    return build_color_widget(color, default)


segment_re = re.compile(r'[a-zA-Z0-9_*-]{0,63}')


class FQDN(object):
    """Validator for a Fully Qualified Domain Name:
    * Allows a leading wildcard (i.e., *.example.com)
    * Total length <= 255
    * Each segment length <= 63
    * Cannot begin or end with -
    * Must be alphanumeric (including _ and -)
    """

    def __call__(self, node, value):
        # While technically legal, it will greatly increase complexity
        # to support this feature of DNS
        value = value.rstrip('.')
        if len(value) > 255:
            raise Invalid(node, 'Domain name is too long.')
        for i, segment in enumerate(value.split('.')):
            if len(segment) > 63:
                raise Invalid(node, 'Segment is too long: %s.' % segment)
            if i > 0 and '*' in segment:
                msg = 'Wildcard only allowed in leading segment.'
                raise Invalid(node, msg)
            elif i == 0 and segment.find('*') > 0:
                msg = 'Wildcard must be first character in segment.'
                raise Invalid(node, msg)
            if segment.startswith('-') or segment.endswith('-'):
                raise Invalid(node, 'Names cannot begin or end with "-".')
            if len(segment_re.findall(segment)[0]) != len(segment):
                raise Invalid(node, 'Invalid segment: "%s".' % segment)


class UserEmail(object):
    """Validator to check email existence in UserProfiles

    If ``msg`` is supplied, it will be the error message to be used when
    raising `colander.Invalid`; otherwise, defaults to 'No user with that email
    address' The ``should_exist`` keyword argument specifies whether the
    validator checks for the email existing or not in the table. It defaults to
    `True`
    """
    def __init__(self, msg=None, should_exist=True, for_edit=False,
                 db_session=None):
        if msg is None:
            msg = "No user with that email address"
        self.msg = msg
        self.should_exist = should_exist
        self.for_edit = for_edit
        self.db_session = db_session

    def __call__(self, node, value):
        # This relies on the current_value attribute being set
        # when the form is created (based on the authenticated username)
        if self.for_edit and value == node.current_value:
            return True
        if self.db_session is not None:
            query = self.db_session.query(UserProfile)
            query = query.filter(UserProfile.email == value)
            exists = bool(query.count())
            if exists != self.should_exist:
                raise Invalid(node, self.msg)


@deferred
def create_user_email_validator(node, kw):
    email_validator = kw.get('email_validator')
    validator = All(
        Email(),
        UserEmail(**email_validator),
    )
    return validator


class DomainName(object):
    """Validator to check for exising domain names in DomainProfiles

    If ``msg`` is supplied, it will be the error message to be used when
    raising `colander.Invalid`; otherwise, defaults to 'A domain with that
    name already exists'

    The ``should_exist`` keyword argument specifies whether the validator
    checks for the domain name existing or not. It defaults to `False`
    """
    def __init__(self, msg=None, should_exist=False, for_edit=False,
                 db_session=None):
        if msg is None:
            msg = "A domain with that name already exists"
        self.msg = msg
        self.should_exist = should_exist
        self.for_edit = for_edit
        self.db_session = db_session

    def __call__(self, node, value):
        # must set current_value to target domain name in edit form
        if self.for_edit and value == node.current_value:
            return True
        if self.db_session is not None:
            query = self.db_session.query(DomainProfile)
            query = query.filter(DomainProfile.name == value)
            exists = bool(query.count())
            if exists != self.should_exist:
                raise Invalid(node, self.msg)


@deferred
def create_domain_validator(node, kw):
    domain_validator = kw.get('domain_validator')
    validator = All(
        FQDN(),
        DomainName(**domain_validator),
    )
    return validator


class UserName(object):
    """Validator to check username existence in UserProfiles

    The ``should_exist`` keyword argument specifies whether the validator
    checks for the username existing or not in the table. It defaults to
    `False`
    """
    def __init__(self, should_exist=False, db_session=None):
        self.should_exist = should_exist
        if should_exist:
            self.msg = "Username does not exist."
        else:
            self.msg = "Username already exists."
        self.db_session = db_session

    def __call__(self, node, value):
        if self.db_session is not None:
            query = self.db_session.query(UserProfile)
            query = query.filter(UserProfile.username == value)
            exists = bool(query.count())
            if exists != self.should_exist:
                raise Invalid(node, self.msg)


@deferred
def create_username_validator(node, kw):
    username_validator = kw.get('username_validator')
    request = kw.get('request')
    if hasattr(request.registry, 'username_validator_class') and \
       request.registry.username_validator_class:
        custom_validator = request.registry.username_validator_class
        validator = All(
            UserName(**username_validator),
            custom_validator(**username_validator),
        )
    else:
        validator = UserName(**username_validator)
    return validator


def usage_policy_validator(value):
    return value is True


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


class Profile(CSRFSchema):
    username = SchemaNode(
        String(),
        validator=create_username_validator,
        description='* We suggest using your first and last name.',
    )
    first_name = SchemaNode(String())
    last_name = SchemaNode(String())
    email = SchemaNode(
        String(),
        title=u'Email Address',
        validator=create_user_email_validator,
        widget=CheckedInputWidget(subject=u'Email Address',
                                  confirm_subject=u'Confirm Email Address'),
    )
    password = SchemaNode(
        String(),
        widget=StrengthValidatingPasswordWidget(),
        description=
        '* Minimum of 8 characters and must include one non-alpha character.',
        validator=create_password_validator,
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


class EditProfileSchema(CSRFSchema):
    username = SchemaNode(
        String(),
        missing='',
        widget=TextInputWidget(template='readonly/textinput'),
    )
    first_name = SchemaNode(String(), required=False)
    last_name = SchemaNode(String(), required=False)
    email = SchemaNode(
        String(),
        title=u'Email Address',
        validator=create_user_email_validator,
        widget=CheckedInputWidget(subject=u'Email Address',
                                  confirm_subject=u'Confirm Email Address'),
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
    target_user = getattr(request, 'target_user', None)
    user = target_user or request.user
    email_validator = dict(should_exist=False,
                           msg="Email address already in use.",
                           db_session=request.db_session)
    username_validator = dict(should_exist=False,
                              db_session=request.db_session)
    if edit:
        email_validator['for_edit'] = True
        # We need to attach the current value of the user's email
        # so we know if they're trying to change it during validation
        schema = EditProfileSchema()
        for fld in schema:
            if fld.name == 'email':
                fld.current_value = user.email
        if request.user.is_superuser:
            is_superuser = SchemaNode(
                Bool(),
                title='Is this user an admin?',
            )
            user_disabled = SchemaNode(
                Bool(),
                title='User disabled?',
            )
            schema['user_disabled'] = user_disabled
            schema['is_superuser'] = is_superuser

        # Can't compare SQLA objects here, so use the usernames.
        # Admin users editing their own profile still need a password.
        username = request.user.username
        target_username = target_user.username
        if username == target_username or not request.user.is_superuser:
            password = SchemaNode(
                String(),
                required=False,
                missing=null,
                description=u"Password only required if changing email.",
                widget=PasswordWidget(),
                title='Password',
                name='password',
            )
            schema['password'] = password
    else:
        schema = Profile()
        if not request.user:
            # Only include these if the user isn't logged in
            agree_to_policy = SchemaNode(
                Bool(),
                title='I agree to the site policy.',
                validator=Function(
                    usage_policy_validator,
                    message='Agreement with the site policy is required.'),
            )
            captcha = SchemaNode(
                String(),
                widget=deferred_recaptcha_widget,
            )
            schema['agree_to_policy'] = agree_to_policy
            schema['captcha'] = captcha
        elif request.user.is_superuser:
            is_superuser = SchemaNode(
                Bool(),
                title='Is this user an admin?',
            )
            schema['is_superuser'] = is_superuser

    form = Form(
        buttons=('submit',),
        resource_registry=password_registry,
        renderer=renderer,
        schema = schema.bind(request=request,
                             email_validator=email_validator,
                             username_validator=username_validator),
        bootstrap_form_style='form-vertical',
    )
    return form


class Domain(CSRFSchema):
    display_name = SchemaNode(
        String(),
        title="Name",
        description="A user-friendly name to identify the domain",
    )
    name = SchemaNode(
        String(),
        title="Domain Name",
        description="Must be a valid Fully Qualified Domain Name",
        validator=create_domain_validator,
    )
    password_valid = SchemaNode(
        Integer(),
        default=-1,
        title="Password valid",
        description="Indicate the length of time, in minutes that a password "
                    "should be valid (a negative value will use the system "
                    "default)",
    )
    primary_color = SchemaNode(
        String(),
        title="Primary Color",
        description=
        "Provide a valid hexidecimal color value, including the '#'. If left "
        "empty, the site default value will be used",
        required=False,
        missing='',
        widget=deferred_primary_color_widget,
    )
    secondary_color = SchemaNode(
        String(),
        title="Secondary Color",
        description=
        "Provide a valid hexidecimal color value, including the '#'. If left "
        "empty, the site default value will be used",
        required=False,
        missing='',
        widget=deferred_secondary_color_widget,
    )


def make_domain_form(request, domain=None):
    edit = False
    primary_color = default_primary_color = request.registry.settings.get(
        'speak_friend.primary_color', DEFAULT_PRIMARY_COLOR)
    secondary_color = default_secondary_color = request.registry.settings.get(
        'speak_friend.secondary_color', DEFAULT_SECONDARY_COLOR)

    if domain is not None:
        edit = True
        if domain.primary_color:
            primary_color = domain.primary_color
        if domain.secondary_color:
            secondary_color = domain.secondary_color

    domain_validator = dict(for_edit=edit,
                            db_session=request.db_session)
    schema = Domain()
    if edit:
        for fld in schema:
            if fld.name == 'name':
                fld.current_value = domain.name
            if fld.name in ['primary_color', 'secondary_color']:
                val = getattr(domain, fld.name, None)
                if val is not None:
                    fld.current_value = val

    return Form(
        schema.bind(
            request=request,
            domain_validator=domain_validator,
            primary_color=primary_color,
            default_primary_color=default_primary_color,
            secondary_color=secondary_color,
            default_secondary_color=default_secondary_color),
        buttons=('submit', 'cancel'),
        bootstrap_form_style='form-vertical',
        renderer=renderer,
        resource_registry=colorpicker_registry,
    )


class PasswordResetRequest(CSRFSchema):
    email = SchemaNode(
        String(),
        title=u'Email Address',
        validator=create_user_email_validator,
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


def make_password_reset_request_form(request):
    email_validator = dict(should_exist=True,
                           db_session=request.db_session)
    schema = PasswordResetRequest()
    password_reset_request_form = Form(
        schema.bind(request=request, email_validator=email_validator),
        bootstrap_form_style='form-vertical',
        buttons=(
            Button('submit', title='Request Password'),
            'cancel'
        ),
    )
    return password_reset_request_form


class Login(CSRFSchema):
    login = SchemaNode(
        String(),
        title='Username or Email',
    )
    password = SchemaNode(
        String(),
        widget=PasswordWidget(),
    )
    remember_me = SchemaNode(
        Bool(),
        title="Remember me?",
        missing=False,
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


def make_login_form(request, action=''):
    schema = Login()
    login_form = Form(
        schema=schema.bind(request=request),
        action=action,
        bootstrap_form_style='form-vertical',
        buttons=(
            Button('submit', title='Log In'),
            'cancel'
        )
    )
    return login_form


class PasswordReset(CSRFSchema):
    password = SchemaNode(
        String(),
        widget=StrengthValidatingPasswordWidget(),
        validator=create_password_validator
    )


def make_password_reset_form(request):
    schema = PasswordReset()
    if request:
        schema = PasswordReset().bind(request=request)
    password_reset_form = Form(
        schema,
        bootstrap_form_style='form-vertical',
        buttons=(
            Button('submit', title='Reset Password'),
        ),
        resource_registry=password_registry,
        renderer=renderer
    )
    return password_reset_form


class PasswordChange(CSRFSchema):
    password = SchemaNode(
        String(),
        widget=PasswordWidget(),
    )
    new_password = SchemaNode(
        String(),
        widget=StrengthValidatingPasswordWidget(),
        description=(
            '* Minimum of 8 characters and must include one non-alpha '
            'character.'
        ),
        validator=create_password_validator
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='.',
        title=u'came_from',
    )


def make_password_change_form(request, admin_change=False):
    schema = PasswordChange()
    if admin_change:
        del schema['password']
    password_reset_form = Form(
        schema=schema.bind(request=request),
        bootstrap_form_style='form-vertical',
        buttons=(
            Button('submit', title='Change Password'),
        ),
        resource_registry=password_registry,
        renderer=renderer
    )
    return password_reset_form


class UserSearch(CSRFSchema):
    query = SchemaNode(
        String(),
        missing='',
        description=
        "Enter all or the start of a user's first name, last name, email "
        "address or username"
    )
    column = SchemaNode(
        String(),
        default='username',
        widget=HiddenWidget()
    )
    order = SchemaNode(
        String(),
        default='asc',
        widget=HiddenWidget()
    )


def make_user_search_form(request):
    schema = UserSearch()
    buttons = [Button('search', title='Search')]
    if 'query' in request.GET:
        buttons += [Button('clear_search', title='Clear Search',
                           type='submit', css_class='btn')]

    user_search_form = Form(
        method="GET",
        formid="usersearch",
        schema=schema.bind(request=request),
        bootstrap_form_style='form-vertical',
        buttons=buttons,
    )
    return user_search_form


class DisableUser(MappingSchema):
    username = SchemaNode(
        String(),
        widget=HiddenWidget(),
    )


def make_disable_user_form(request):
    schema = DisableUser()
    # This form will be on a page with multiple forms,
    # so we have to set the formid attribute for the ajax
    # stuff to work.
    disable_user_form = Form(
        schema=schema.bind(request=request),
        buttons=(Button('submit', title='Yes'),
                 Button('cancel', title='No')),
        formid='disable-form',
    )
    return disable_user_form


class Authorization(CSRFSchema):
    description = SchemaNode(
        String(),
        title=u'Add an authorization',
        description=u'Application Name or Description',
        # validator=Regex(r'\S', msg="Be nice!")
    )


def make_new_authorization_form(request):
    schema = Authorization()
    new_authoization_form = Form(
        schema=schema.bind(request=request),
        buttons=(Button(u'submit', title=u'Create'),),
    )
    return new_authoization_form
