# Views related to account management (creating, editing, deactivating)

from deform import Form, ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.renderers import render_to_response
from pyramid.security import authenticated_userid, forget, remember
from pyramid.view import view_defaults

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from speak_friend.events import AccountCreated
from speak_friend.forms.profiles import make_password_reset_request_form
from speak_friend.forms.controlpanel import password_reset_schema
from speak_friend.forms.profiles import make_profile_form, make_login_form
from speak_friend.models import DBSession
from speak_friend.models.profiles import ResetToken
from speak_friend.models.profiles import UserProfile
from speak_friend.views.controlpanel import ControlPanel


@view_defaults(route_name='create_profile')
class CreateProfile(object):
    def __init__(self, request):
        self.request = request
        self.session = DBSession()
        self.pass_ctx = request.registry.password_context

    def get_referrer(self):
        came_from = self.request.referrer
        if not came_from:
            came_from = '/'
        return came_from

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()
        profile_form = make_profile_form()

        try:
            appstruct = profile_form.validate(controls)  # call validate
        except ValidationFailure, e:
            return {'rendered_form': e.render()}

        hashed_pw = self.pass_ctx.encrypt(appstruct['password'])

        profile = UserProfile(appstruct['username'],
                              appstruct['first_name'],
                              appstruct['last_name'],
                              appstruct['email'],
                              hashed_pw,
                              hashed_pw,
                              0,
                              False
        )
        self.session.add(profile)
        self.request.session.flash('Account successfully created!',
                                   queue='success')
        self.request.registry.notify(AccountCreated(self.request, profile))
        if appstruct['came_from']:
            return HTTPFound(location=appstruct['came_from'])
        else:
            url = self.request.route_url('home')
            return HTTPFound(location=url)

    def get(self, success=False):
        if success:
            return {'forms': [], 'rendered_form': '', 'success': True}
        profile_form = make_profile_form()

        return {
            'forms': [profile_form],
            'rendered_form': profile_form.render({
                'came_from': self.get_referrer(),
            }),
        }


# XXX Only logged in users should have permission
@view_defaults(route_name='edit_profile')
class EditProfile(object):

    def __init__(self, request):
        self.request = request
        self.target_username = request.matchdict['username']
        self.current_username = authenticated_userid(request)
        self.session = DBSession()

    def get_referrer(self):
        came_from = self.request.referrer
        if not came_from:
            came_from = '/'
        return came_from

    def error(self):
        return HTTPFound("You are not allowed to access this resource")

    def get(self):
        # Make sure the user who is editing is an admin, or the user requested
        #   Return an error page if not
        # Fetch the user information from the DB
        # Create an appstruct
        # Pass the appstruct to form.render(appstruct)
        user = self.session.query(UserProfile).filter(
                UserProfile.username==self.current_username).first()
        if not (self.target_username == self.current_username or
            user.is_superuser):
            return self.error()

        appstruct = user.get_appstruct()
        form = make_profile_form()
        return {
            'forms': [form],
            'rendered_form': form.render(appstruct),
        }


def token_expired(request):
    cp = ControlPanel(request)
    token_duration = None
    current = cp.saved_sections.get(password_reset_schema.name)
    if current and current.panel_values:
        token_duration = current.panel_values['token_duration']
    else:
        for child in password_reset_schema.children:
            if child.name == 'token_duration':
                token_duration = child.default

    request.response.status = "400 Bad Request"
    reset_url = request.route_url('request_password')
    return {'reset_url': reset_url, 'token_duration': token_duration}


# FIXME: attach appropriate permissions
@view_defaults(route_name='request_password')
class RequestPassword(object):
    def __init__(self, request):
        self.request = request
        self.session = DBSession()
        self.frm = make_password_reset_request_form()
        self.path = 'speak_friend:templates/email/password_reset_notification.pt'
        settings = request.registry.settings
        self.subject = "%s: Reset password" % settings['site_name']
        self.sender = settings['site_from']
        self.token_duration = None
        cp = ControlPanel(request)

        current = cp.saved_sections.get(password_reset_schema.name)
        if current and current.panel_values:
            self.token_duration = current.panel_values['token_duration']
        else:
            for child in password_reset_schema.children:
                if child.name == 'token_duration':
                    self.token_duration = child.default

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()
        try:
            controls = self.request.POST.items()
            captured = self.frm.validate(controls)
            self.notify(captured)
            url = self.request.route_url('home')
            return HTTPFound(location=url)
        except ValidationFailure as e:
            # the submitted values could not be validated
            html = e.render()

        return {
            'forms': [self.frm],
            'rendered_form': html,
        }

    def get(self):
        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render(),
        }

    def notify(self, captured):
        query = self.session.query(UserProfile)
        query = query.filter(UserProfile.email==captured['email'])
        profile = query.first()

        mailer = get_mailer(self.request)
        reset_token = ResetToken(profile.username)
        response = render_to_response(self.path,
                                      {'token': reset_token.token},
                                      self.request)
        self.session.merge(reset_token)
        message = Message(subject=self.subject,
                          sender=self.sender,
                          recipients=[profile.full_email],
                          html=response.unicode_body)
        mailer.send(message)
        self.request.session.flash('A link to reset your password has been sent to your email. Please check.',
                                   queue='success')


@view_defaults(route_name='reset_password')
class ResetPassword(object):
    def __init__(self, request):
        """Stub for now
        """

    def post(self):
        """Stub for now
        """

    def get(self):
        """Stub for now
        """

    def notify(self, captured):
        """Notify interested parties that the user successfully reset their
        pasword.
        """


@view_defaults(route_name='login')
class LoginView(object):
    def __init__(self, request):
        self.request = request
        self.pass_ctx = request.registry.password_context
        self.error_string = 'Username or password is invalid.'
        self.frm = make_login_form()

    def verify_password(self, password, saved_hash, user):
        if not user:
            return False

        if self.pass_ctx.verify(password, saved_hash):
            if self.pass_ctx.needs_update(saved_hash):
                new_hash = self.pass_ctx.encrypt(password)
                user.password_hash = new_hash
                DBSession().add(user)
            passes = True
        else:
            passes = False
        return passes

    def get(self):
        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render()
        }

    def login_error(self, msg):
        self.request.session.flash(msg, queue='error')
        return self.get()

    def post(self):
        url = self.request.current_route_url()
        referrer = self.request.url
        if referrer == url:
            referrer = '/'

        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()

        try:
            appstruct = self.frm.validate(controls)
        except ValidationFailure:
            return self.login_error(self.error_string)

        login = appstruct['login']
        password = appstruct['password']

        user = DBSession.query(UserProfile).\
                filter(UserProfile.username==login).first()

        if user:
            saved_hash = user.password_hash
        else:
            return self.login_error(self.error_string)

        if not self.verify_password(password, saved_hash, user):
            return self.login_error(self.error_string)

        headers = remember(self.request, login)
        return HTTPFound(location=referrer, headers=headers)


def logout(request):
    referrer = request.referrer.url
    if not referrer:
        referrer = '/'
    headers = forget(request)
    return HTTPFound(referrer, headers=headers)
