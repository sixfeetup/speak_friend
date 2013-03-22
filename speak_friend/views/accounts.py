# Views related to account management (creating, editing, deactivating)
from datetime import timedelta
from uuid import UUID

import colander
from deform import ValidationFailure

from psycopg2 import DataError

from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.httpexceptions import HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.security import forget, remember
from pyramid.view import view_defaults

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from sqlalchemy import func

from speak_friend.events import AccountCreated
from speak_friend.events import AccountDisabled
from speak_friend.events import AccountEnabled
from speak_friend.events import AccountLocked
from speak_friend.events import AccountUnlocked
from speak_friend.events import LoggedIn
from speak_friend.events import LoggedOut
from speak_friend.events import LoginFailed
from speak_friend.events import ProfileChanged
from speak_friend.forms.controlpanel import MAX_DOMAIN_ATTEMPTS
from speak_friend.forms.controlpanel import authentication_schema
from speak_friend.forms.profiles import make_password_reset_form
from speak_friend.forms.profiles import make_password_reset_request_form
from speak_friend.forms.profiles import make_password_change_form
from speak_friend.forms.profiles import make_profile_form, make_login_form
from speak_friend.models.profiles import ResetToken
from speak_friend.models.profiles import UserProfile
from speak_friend.views.admin import UserSearch
from speak_friend.views.controlpanel import ControlPanel
from speak_friend.utils import get_referrer


@view_defaults(route_name='create_profile')
class CreateProfile(object):
    def __init__(self, request):
        self.request = request
        self.pass_ctx = request.registry.password_context

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()
        profile_form = make_profile_form(self.request)

        try:
            appstruct = profile_form.validate(controls)  # call validate
        except ValidationFailure, e:
            return {
                'forms': [profile_form],
                'rendered_form': e.render(),
            }

        hashed_pw = self.pass_ctx.encrypt(appstruct['password'])

        profile = UserProfile(appstruct['username'],
                              appstruct['first_name'],
                              appstruct['last_name'],
                              appstruct['email'],
                              hashed_pw,
                              None,
                              0,
                              False
        )
        self.request.db_session.add(profile)
        self.request.registry.notify(AccountCreated(self.request, profile))
        self.request.session.flash('Your account has been created successfully.',
                                   queue='success')

        headers = remember(self.request, appstruct['username'])
        logged_in = LoggedIn(self.request,
                             profile,
                             came_from=get_referrer(self.request))
        self.request.registry.notify(logged_in)
        self.request.response.headerlist.extend(headers)

        came_from = appstruct.get('came_from', '')
        local_request = came_from.startswith(self.request.host_url)

        if came_from and not local_request:
            return HTTPFound(location=appstruct['came_from'], headers=headers)
        else:
            url = self.request.route_url('home')
            return HTTPFound(location=url, headers=headers)

    def get(self, success=False):
        if success:
            return {'forms': [], 'rendered_form': '', 'success': True}
        profile_form = make_profile_form(self.request)

        return {
            'forms': [profile_form],
            'rendered_form': profile_form.render({
                'came_from': get_referrer(self.request),
            }),
        }


@view_defaults(route_name='edit_profile')
class EditProfile(object):

    def __init__(self, request):
        self.request = request
        self.target_username = request.matchdict['username']
        self.pass_ctx = request.registry.password_context
        query = self.request.db_session.query(UserProfile)
        self.target_user = query.get(self.target_username)
        if self.target_user is None:
            raise HTTPNotFound()

    def get_extended_data(self):
        """Provide a hook to extend the dict returned by the view.
        Any new values will require that the view template is overriden
        to use them.
        """
        return None

    def verify_password(self, password, saved_hash, user):
        if not user:
            return False

        kwargs = {}
        if user.password_salt:
            # if the user has a password salt stored, we'll need to
            # pass it as a keyword arg to the verify method
            kwargs['salt'] = user.password_salt

        if self.pass_ctx.verify(password, saved_hash, **kwargs):
            if self.pass_ctx.needs_update(saved_hash):
                new_hash = self.pass_ctx.encrypt(password)
                user.password_hash = new_hash
                # if the user had a password_salt stored, we want to wipe it
                # out so that the salt auto-generated by passlib will
                # take over
                user.password_salt = None
                self.request.db_session.add(user)
            passes = True
        else:
            passes = False
        return passes

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()
        self.request.target_user = self.target_user
        profile_form = make_profile_form(self.request, edit=True)

        activity_detail = {}

        try:
            appstruct = profile_form.validate(controls)  # call validate
        except ValidationFailure, e:
            # Don't leak hash information
            if ('password' in profile_form.cstruct
                and profile_form.cstruct['password'] != ''):
                profile_form.cstruct['password'] = ''
            data = {
                'forms': [profile_form],
                'rendered_form': e.render(),
                'target_username': self.target_username,
            }
            ex_data = self.get_extended_data()
            if ex_data:
                data.update(ex_data)
            return data

        same_user = self.request.user == self.target_user

        if same_user:
            password = appstruct.get('password', colander.null)
            if password == colander.null:
                password = ''

            valid_pass = self.verify_password(password,
                                              self.target_user.password_hash,
                                              self.target_user)
        if not same_user and self.request.user.is_superuser:
            # Let admins edit email addresses w/o a password check
            valid_pass = True

        failed = False
        if (self.target_user.email != appstruct['email'] and
            valid_pass):
            activity_detail['old_address'] = [field.current_value
                        for field in profile_form.schema
                        if field.name == 'email'
            ][0]
            activity_detail['new_address'] = appstruct['email']
            self.target_user.email = appstruct['email']
        elif (self.target_user.email != appstruct['email']
              and not valid_pass):
            self.request.session.flash('Must provide the correct password to edit email addresses.',
                                      queue='error')
            failed = True

        if self.target_user.first_name != appstruct['first_name']:
            self.target_user.first_name = appstruct['first_name']
            activity_detail['first_name'] = appstruct['first_name']
        if self.target_user.last_name != appstruct['last_name']:
            self.target_user.last_name = appstruct['last_name']
            activity_detail['last_name'] = appstruct['last_name']

        if self.request.user.is_superuser and 'user_disabled' in appstruct:
            self.target_user.admin_disabled = appstruct['user_disabled']
            if appstruct['user_disabled']:
                self.request.registry.notify(
                    AccountDisabled(self.request,
                                    self.target_user,
                                    **activity_detail)
                )
            else:
                self.request.registry.notify(
                    AccountEnabled(self.request,
                                    self.target_user,
                                    **activity_detail)
                )

        self.request.db_session.add(self.target_user)
        if not failed:
            self.request.registry.notify(ProfileChanged(self.request,
                                                        self.target_user,
                                                        **activity_detail))
            self.request.session.flash('Account successfully modified!',
                                       queue='success')
        if self.request.user.is_superuser:
            return HTTPFound(self.request.route_url('user_search'))
        else:
            return self.get()

    def get(self):
        appstruct = self.target_user.make_appstruct()
        if self.request.user.is_superuser:
            appstruct['user_disabled'] = self.target_user.admin_disabled

        self.request.target_user = self.target_user
        form = make_profile_form(self.request, edit=True)
        data = {
            'forms': [form],
            'rendered_form': form.render(appstruct),
            'target_username': self.target_username,
        }
        extended_data = self.get_extended_data()
        if extended_data:
            data.update(extended_data)
        return data


@view_defaults(route_name='change_password')
class ChangePassword(object):
    def __init__(self, request):
        self.request = request
        self.target_username = request.matchdict['username']
        self.pass_ctx = request.registry.password_context
        query = self.request.db_session.query(UserProfile)
        self.target_user = query.get(self.target_username)
        if self.target_user is None:
            raise HTTPNotFound()

    def verify_password(self, password, saved_hash, user):
        if not user:
            return False

        kwargs = {}
        if user.password_salt:
            # if the user has a password salt stored, we'll need to
            # pass it as a keyword arg to the verify method
            kwargs['salt'] = user.password_salt

        if self.pass_ctx.verify(password, saved_hash, **kwargs):
            if self.pass_ctx.needs_update(saved_hash):
                new_hash = self.pass_ctx.encrypt(password)
                user.password_hash = new_hash
                # if the user had a password_salt stored, we want to wipe it
                # out so that the salt auto-generated by passlib will
                # take over
                user.password_salt = None
                self.request.db_session.add(user)
            passes = True
        else:
            passes = False
        return passes

    def get(self):
        form = make_password_change_form()
        return {
            'forms': [form],
            'rendered_form': form.render(),
            'target_username': self.target_username,
        }

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()
        form = make_password_change_form(request=self.request)

        try:
            appstruct = form.validate(controls)  # call validate
        except ValidationFailure, e:
            # Don't leak hash information
            if ('password' in form.cstruct
                and form.cstruct['password'] != ''):
                form.cstruct['password'] = ''
            return {
                'forms': [form],
                'rendered_form': e.render(),
                'target_username': self.target_username,
            }

        password = appstruct['password']
        if password == colander.null:
            password = ''

        valid_pass = self.verify_password(password,
                                          self.target_user.password_hash,
                                          self.target_user)

        new_hash = self.pass_ctx.encrypt(appstruct['new_password'])

        if valid_pass:
            self.target_user.password_hash = new_hash
            self.request.db_session.add(self.target_user)
            self.request.session.flash('Account successfully modified!',
                                       queue='success')
        else:
            self.request.session.flash('Incorrect password.',
                                       queue='error')
        return self.get()

def token_expired(request):
    cp = ControlPanel(request)
    token_duration = None
    current = cp.saved_sections.get(authentication_schema.name)
    if current and current.panel_values:
        token_duration = current.panel_values['token_duration']
    else:
        for child in authentication_schema.children:
            if child.name == 'token_duration':
                token_duration = child.default
    request.response.status = "400 Bad Request"
    url = request.route_url('request_password')
    return {
        'token_duration': token_duration,
        'request_reset_url': url,
    }


def token_invalid(request):
    request.response.status = "400 Bad Request"
    url = request.route_url('request_password')
    return {
        'request_reset_url': url,
    }


@view_defaults(route_name='request_password')
class RequestPassword(object):
    def __init__(self, request):
        self.request = request
        self.frm = make_password_reset_request_form(request)
        self.path = 'speak_friend:templates/email/password_reset_notification.pt'
        settings = request.registry.settings
        self.subject = "%s: Reset password" % settings['site_name']
        self.sender = settings['site_from']

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
            'rendered_form': self.frm.render({
                'came_from': get_referrer(self.request),
            }),
        }

    def notify(self, captured):
        query = self.request.db_session.query(UserProfile)
        query = query.filter(UserProfile.email==captured['email'])
        profile = query.first()

        mailer = get_mailer(self.request)
        reset_token = ResetToken(profile.username, captured['came_from'])
        response = render_to_response(self.path,
                                      {'token': reset_token.token},
                                      self.request)
        self.request.db_session.add(reset_token)
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
        self.request = request
        self.token_duration = None
        cp = ControlPanel(request)

        current = cp.saved_sections.get(authentication_schema.name)
        if current and current.panel_values:
            self.token_duration = current.panel_values['token_duration']
        else:
            for child in authentication_schema.children:
                if child.name == 'token_duration':
                    self.token_duration = child.default


    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        token = self.request.matchdict['token']
        try:
            reset_token = self.check_token(token)
            if reset_token is None:
                url = self.request.route_url('token_expired')
                return HTTPFound(location=url)
        except (DataError, ValueError), err:
            url = self.request.route_url('token_invalid')
            return HTTPFound(location=url)

        password_reset_form = make_password_reset_form(self.request)

        try:
            controls = self.request.POST.items()
            captured = password_reset_form.validate(controls)
            pw = captured['password']
            pw_hash = self.request.registry.password_context.encrypt(pw)
            reset_token.user.password_hash = pw_hash
            token_query = self.request.db_session.query(ResetToken)
            token_query.filter(
                ResetToken.username==reset_token.user.username).delete()

            reset_token.user.login_attempts = 0
            reset_token.user.locked = False
            self.request.registry.notify(AccountUnlocked(self.request,
                                                         reset_token.user))
            headers = remember(self.request, reset_token.user.username)
            self.request.response.headerlist.extend(headers)
            self.notify(reset_token.user)
            self.request.session.flash('Password successfully reset!',
                                       queue='success')
            url = self.request.route_url('home')
            self.request.registry.notify(LoggedIn(self.request,
                                                  reset_token.user,
                                                  came_from=reset_token.came_from))

            if reset_token.came_from:
                return HTTPFound(location=reset_token.came_from,
                                 headers=headers)
            else:
                url = self.request.route_url('home')
                return HTTPFound(location=url, headers=headers)
        except ValidationFailure as e:
            # the submitted values could not be validated
            html = e.render()

        return {
            'forms': [password_reset_form],
            'rendered_form': html,
        }

    def get(self):
        token = self.request.matchdict['token']
        try:
            reset_token = self.check_token(token)
            if reset_token is None:
                url = self.request.route_url('token_expired')
                return HTTPFound(location=url)
        except (DataError, ValueError), err:
            url = self.request.route_url('token_invalid')
            return HTTPFound(location=url)

        password_reset_form = make_password_reset_form()

        return {
            'forms': [password_reset_form],
            'rendered_form': password_reset_form.render(),
        }

    def notify(self, user_profile):
        """Notify interested parties that the user successfully reset their
        pasword.
        """

    def check_token(self, token):
        """Check UID token against database.
        Can raise either ValueError or DataError if parsing the token as a UUID
        fails in either Python or PostgreSQL, respectively.
        """
        # Check UID validity at Python level to avoid wasting a call to the db
        uid = UUID(token)
        query = self.request.db_session.query(ResetToken)
        query = query.filter(ResetToken.token==uid)
        ts = ResetToken.generation_ts + timedelta(minutes=self.token_duration)
        query = query.filter(ts >= func.current_timestamp())
        results = query.first()
        return results


@view_defaults(route_name='login')
class LoginView(object):
    def __init__(self, request):
        self.request = request
        self.pass_ctx = request.registry.password_context
        self.invalid_error = 'Username or password is invalid.'
        self.locked_error = 'Your account has been disabled. ' \
                            'Check your email for instructions to reset your password.'
        query = self.request.GET.items()
        action = request.current_route_url(_query=query)
        self.frm = make_login_form(action)
        cp = ControlPanel(request)
        self.max_attempts = None
        current = cp.saved_sections.get(authentication_schema.name)
        if current and current.panel_values:
            self.max_attempts = current.panel_values['max_attempts']
        else:
            self.max_attempts = MAX_DOMAIN_ATTEMPTS


    def verify_password(self, password, saved_hash, user):
        if not user:
            return False

        kwargs = {}
        if user.password_salt:
            # if the previous user has a password salt stored, we'll need to
            # pass it as a keyword arg to the verify method
            kwargs['salt'] = user.password_salt

        if self.pass_ctx.verify(password, saved_hash, **kwargs):
            if self.pass_ctx.needs_update(saved_hash):
                new_hash = self.pass_ctx.encrypt(password)
                user.password_hash = new_hash
                # if the user had a password_salt stored, we want to wipe it
                # out so that the salt auto-generated by passlib will
                # take over
                user.password_salt = None
                self.request.db_session.add(user)
            passes = True
        else:
            passes = False
        return passes

    def get(self):
        #if ('password' in self.frm.cstruct
        #    and self.frm.cstruct['password'] != ''):
        #    self.frm.cstruct['password'] = ''
        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render({
                'came_from': get_referrer(self.request),
            }),
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
            return self.login_error(self.invalid_error)

        login = appstruct['login']
        password = appstruct['password']

        query = self.request.db_session.query(UserProfile)
        query = query.filter((UserProfile.username==login) | \
                             (UserProfile.email==login))
        user = query.first()

        if user:
            saved_hash = user.password_hash
        else:
            return self.login_error(self.error_string)

        if user.locked:
            return self.login_error(self.locked_error)
        elif not self.verify_password(password, saved_hash, user):
            self.request.registry.notify(LoginFailed(self.request, user))
            # Don't just use += 1, as that is subject to race conditions
            # with concurrent updates
            user.login_attempts = UserProfile.login_attempts + 1
            if user.login_attempts >= self.max_attempts:
                user.locked = True
                self.request.registry.notify(AccountLocked(self.request, user))
                return self.login_error(self.locked_error)
            else:
                return self.login_error(self.invalid_error)

        if user.login_attempts > 0:
            user.login_attempts = 0
            user.locked = False
            self.request.registry.notify(AccountUnlocked(self.request, user))

        headers = remember(self.request, user.username)
        self.request.response.headerlist.extend(headers)

        self.request.registry.notify(LoggedIn(self.request, user,
                                              came_from=appstruct['came_from']))

        came_from = appstruct.get('came_from', '')
        local_request = came_from.startswith(self.request.host_url)

        if came_from and not local_request:
            return HTTPFound(location=appstruct['came_from'], headers=headers)
        else:
            url = self.request.route_url('home')
            return HTTPFound(location=url, headers=headers)


def logout(request, return_to=None):
    # XXX This should really check permissions on the destination first.
    if return_to is None:
        referrer = get_referrer(request)
    else:
        referrer = return_to
    request.registry.notify(LoggedOut(request, request.user))
    headers = forget(request)
    return HTTPFound(referrer, headers=headers)
