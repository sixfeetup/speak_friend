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
        query = self.db_session.query(UserProfile)
        query = query.filter(UserProfile.email==value)
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
        query = self.db_session.query(DomainProfile)
        query = query.filter(DomainProfile.name==value)
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

    The ``should_exist`` keyword argument specifies whether the validator checks for the
    username existing or not in the table. It defaults to `False`
    """
    def __init__(self, should_exist=False, db_session=None):
        self.should_exist = should_exist
        if should_exist == True:
            self.msg = "Username does not exist."
        else:
            self.msg = "Username already exists."
        self.db_session = db_session

    def __call__(self, node, value):
        query = self.db_session.query(UserProfile)
        query = query.filter(UserProfile.username==value)
        exists = bool(query.count())
        if exists != self.should_exist:
            raise Invalid(node, self.msg)


@deferred
def create_username_validator(node, kw):
    username_validator = kw.get('username_validator')
    validator = UserName(**username_validator)
    return validator

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
        validator=create_username_validator,
        description='* we suggest using your first and last name',
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
        description='* Minimum of 8 characters and must include one non-alpha character.',
        validator=create_password_validator,
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
                validator=Function(usage_policy_validator,
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


class Domain(MappingSchema):
    name = SchemaNode(
        String(),
        title="Domain Name",
        description="Must be a valid Fully Qualified Domain Name",
        validator=create_domain_validator,
    )
    password_valid = SchemaNode(
        Integer(),
        title="Password valid",
        description="Indicate the length of time, in minutes that a password "
                    "should be valid (a negative value will use the system "
                    "default)",
    )


def make_domain_form(request, domain=None):
    edit=False
    if domain is not None:
        edit=True
    domain_validator = dict(for_edit=edit,
                            db_session=request.db_session)
    schema = Domain()
    if edit:
        for fld in schema:
            if fld.name == 'name':
                fld.current_value = domain.name

    return Form(
        schema.bind(request=request, domain_validator=domain_validator),
        buttons=('submit', 'cancel'),
        bootstrap_form_style='form-vertical',
    )


class PasswordResetRequest(MappingSchema):
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


class Login(MappingSchema):
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
        required=False,
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
        ),
        resource_registry=password_registry,
        renderer=renderer
    )
    return password_reset_form


class UserSearch(MappingSchema):
    query = SchemaNode(
        String(),
        missing='',
        description="Enter all or the start of a user's first name, last name, email address or username"
    )


def make_user_search_form(request=None):
    schema = UserSearch()
    if request:
        schema = UserSearch().bind(request=request)
    user_search_form = Form(
        schema,
        method="GET",
        formid="usersearch",
        bootstrap_form_style='form-vertical',
        buttons=(Button('submit', title='Search'), )
    )
    return user_search_form


class DisableUser(MappingSchema):
    username = SchemaNode(
        String(),
        widget=HiddenWidget(),
    )


def make_disable_user_form(request=None):
    schema = DisableUser()
    # This form will be on a page with multiple forms,
    # so we have to set the formid attribute for the ajax
    # stuff to work.
    disable_user_form = Form(
        schema,
        buttons=(Button('submit', title='Yes'),
                 Button('cancel', title='No')
        ),
        formid='disable-form',
    )
    return disable_user_form
