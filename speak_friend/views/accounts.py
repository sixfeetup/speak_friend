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
from speak_friend.events import PasswordRequested
from speak_friend.events import PasswordReset
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
        self.login_view = LoginView(request)
        self.frm = make_profile_form(self.request)

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()

        try:
            appstruct = self.frm.validate(controls)  # call validate
        except ValidationFailure, e:
            return {
                'forms': [self.frm],
                'rendered_form': e.render(),
            }

        hashed_pw = self.login_view.pass_ctx.encrypt(appstruct['password'])

        profile = UserProfile(appstruct['username'],
                              appstruct['first_name'],
                              appstruct['last_name'],
                              appstruct['email'],
                              hashed_pw,
                              None,
                              0,
                              False,
                              appstruct.get('is_superuser', False),
        )
        self.request.db_session.add(profile)
        self.request.registry.notify(AccountCreated(self.request, profile))

        if self.request.user:
            headers = []
            self.request.session.flash('You successfully created an account for: %s.' % profile.full_name,
                                       queue='success')
            if self.request.user.is_superuser:
                return HTTPFound(self.request.route_url('user_search'))
        else:
            self.request.session.flash('Your account has been created successfully.',
                                       queue='success')
            # Only take action if the user is not already logged in
            # (i.e., an admin is creating a new account)
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

        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render({
                'came_from': get_referrer(self.request),
            }),
        }


@view_defaults(route_name='edit_profile')
class EditProfile(object):

    def __init__(self, request, max_attempts=None):
        self.request = request
        self.target_username = request.matchdict['username']
        query = self.request.db_session.query(UserProfile)
        self.target_user = query.get(self.target_username)
        request.target_user = self.target_user
        self.login_view = LoginView(request, max_attempts)
        if self.target_user is None:
            raise HTTPNotFound()
        self.frm = make_profile_form(self.request, edit=True)

    def get_extended_data(self):
        """Provide a hook to extend the dict returned by the view.
        Any new values will require that the view template is overriden
        to use them.
        """
        return None

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()
        self.request.target_user = self.target_user

        activity_detail = {}

        try:
            appstruct = self.frm.validate(controls)  # call validate
        except ValidationFailure, e:
            # Don't leak hash information
            if ('password' in self.frm.cstruct
                and self.frm.cstruct['password'] != ''):
                self.frm.cstruct['password'] = ''
            data = {
                'forms': [self.frm],
                'rendered_form': e.render(),
                'target_username': self.target_username,
            }
            ex_data = self.get_extended_data()
            if ex_data:
                data.update(ex_data)
            return data

        same_user = self.request.user.username == self.target_user.username

        valid_pass = False
        if same_user:
            password = appstruct.get('password', colander.null)
            if password == colander.null:
                password = ''

            valid_pass = self.login_view.verify_password(password,
                                                         self.target_user.password_hash,
                                                         self.target_user)
        if (not same_user) and self.request.user.is_superuser:
            # Let admins edit email addresses w/o a password check
            valid_pass = True

        failed = False
        if (self.target_user.email != appstruct['email'] and
            valid_pass):
            activity_detail['old_address'] = [field.current_value
                        for field in self.frm.schema
                        if field.name == 'email'
            ][0]
            activity_detail['new_address'] = appstruct['email']
            self.target_user.email = appstruct['email']
        elif (self.target_user.email != appstruct['email']
              and not valid_pass):
            self.request.session.flash('Must provide the correct password to edit email addresses.',
                                      queue='error')
            failed = True

        for fname in ('first_name', 'last_name', 'is_superuser'):
            fval = appstruct.get(fname)
            if getattr(self.target_user, fname) != fval:
                setattr(self.target_user, fname, fval)
                activity_detail[fname] = fval

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

        if same_user:
            # Invalidate the current token
            self.request.session.new_csrf_token()
            self.request.session.save()

        self.request.db_session.add(self.target_user)

        if not failed:
            self.request.registry.notify(ProfileChanged(self.request,
                                                        self.target_user,
                                                        **activity_detail))
            self.request.session.flash('Account successfully modified!',
                                       queue='success')
        if self.request.user.is_superuser and not failed:
            if 'user_search' in appstruct['came_from']:
                redirect = HTTPFound(appstruct['came_from'])
            else:
                redirect = HTTPFound(self.request.route_url('user_search'))
            return redirect
        else:
            return self.get()

    def get(self):
        appstruct = self.target_user.make_appstruct()
        if self.request.referer:
            appstruct['came_from'] = self.request.referer
        if self.request.user.is_superuser:
            appstruct['user_disabled'] = self.target_user.admin_disabled
            appstruct['is_superuser'] = self.target_user.is_superuser

        self.request.target_user = self.target_user
        data = {
            'forms': [self.frm],
            'rendered_form': self.frm.render(appstruct),
            'target_username': self.target_username,
        }
        extended_data = self.get_extended_data()
        if extended_data:
            data.update(extended_data)
        return data


@view_defaults(route_name='change_password')
class ChangePassword(object):
    def __init__(self, request, max_attempts=None):
        self.request = request
        self.target_username = request.matchdict['username']
        query = self.request.db_session.query(UserProfile)
        self.target_user = query.get(self.target_username)
        if self.target_user is None:
            raise HTTPNotFound()
        self.login_view = LoginView(request, max_attempts)
        self.frm = make_password_change_form(request)

    def get(self):
        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render(),
            'target_username': self.target_username,
        }

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()

        try:
            appstruct = self.frm.validate(controls)  # call validate
        except ValidationFailure, e:
            # Don't leak hash information
            if ('password' in self.frm.cstruct
                and self.frm.cstruct['password'] != ''):
                self.frm.cstruct['password'] = ''
            return {
                'forms': [self.frm],
                'rendered_form': e.render(),
                'target_username': self.target_username,
            }

        password = appstruct['password']
        if password == colander.null:
            password = ''

        valid_pass = self.login_view.verify_password(password,
                                                     self.target_user.password_hash,
                                                     self.target_user)

        new_hash = self.login_view.pass_ctx.encrypt(appstruct['new_password'])

        if valid_pass:
            self.target_user.password_hash = new_hash
            self.request.db_session.add(self.target_user)
            self.request.session.flash('Account successfully modified!',
                                       queue='success')
            # Invalidate the current token
            self.request.session.new_csrf_token()
            self.request.session.save()
            self.request.registry.notify(PasswordReset(self.request,
                                                       self.target_user))
        else:
            self.request.session.flash('Incorrect password.',
                                       queue='error')
        return self.get()

def token_expired(request):
    cp = ControlPanel(request)
    token_duration = cp.get_value(authentication_schema.name, 'token_duration')
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

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()
        try:
            controls = self.request.POST.items()
            captured = self.frm.validate(controls)
            query = self.request.db_session.query(UserProfile)
            query = query.filter(UserProfile.email==captured['email'])
            profile = query.first()
            self.request.registry.notify(PasswordRequested(self.request,
                                                           profile,
                                                           came_from=captured['came_from']))
            self.request.session.flash('A link to reset your password has been sent to your email. Please check.',
                                       queue='success')
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


@view_defaults(route_name='reset_password')
class ResetPassword(object):
    def __init__(self, request):
        self.request = request
        cp = ControlPanel(request)
        self.token_duration = cp.get_value(authentication_schema.name,
                                           'token_duration')
        self.login_view = LoginView(request)
        self.frm = make_password_reset_form(self.request)

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

        if reset_token.user.admin_disabled:
            self.request.session.flash(self.login_view.disabled_error,
                                       queue='error')
            return self.get()


        try:
            controls = self.request.POST.items()
            captured = self.frm.validate(controls)
            pw = captured['password']
            pw_hash = self.request.registry.password_context.encrypt(pw)
            reset_token.user.password_hash = pw_hash
            reset_token.user.password_salt = None
            token_query = self.request.db_session.query(ResetToken)
            token_query.filter(
                ResetToken.username==reset_token.user.username).delete()

            reset_token.user.login_attempts = 0
            headers = remember(self.request, reset_token.user.username)
            self.request.response.headerlist.extend(headers)
            self.request.session.flash('Password successfully reset!',
                                       queue='success')
            if reset_token.user.locked:
                reset_token.user.locked = False
                self.request.registry.notify(AccountUnlocked(self.request,
                                                             reset_token.user))
            # Invalidate the current token
            self.request.session.new_csrf_token()
            self.request.session.save()
            self.request.registry.notify(PasswordReset(self.request,
                                                       reset_token.user))
            self.request.registry.notify(LoggedIn(self.request,
                                                  reset_token.user,
                                                  came_from=reset_token.came_from))

            from_reset_url = reset_token.token not in reset_token.came_from
            if reset_token.came_from and not from_reset_url:
                return HTTPFound(location=reset_token.came_from,
                                 headers=headers)
            else:
                url = self.request.route_url('home')
                return HTTPFound(location=url, headers=headers)
        except ValidationFailure as e:
            # the submitted values could not be validated
            html = e.render()

        return {
            'forms': [self.frm],
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

        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render(),
        }

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
    def __init__(self, request, max_attempts=None):
        self.request = request
        self.pass_ctx = request.registry.password_context
        contact_url = request.route_url('contact_us')
        contact_link = '<a href="%s">contact us</a>' % contact_url
        self.disabled_error = "Your account has been disabled. Please %s if you'd like us to reactivate your account." % contact_link
        self.invalid_error = 'Username or password is invalid.'
        self.locked_error = 'Your account has been disabled. ' \
                            'Check your email for instructions to reset your password.'
        query = self.request.GET.items()
        action = request.route_url('login', _query=query)
        self.frm = make_login_form(request, action)
        if max_attempts is None:
            cp = ControlPanel(request)
            self.max_attempts = cp.get_value(authentication_schema.name,
                                             'max_attempts',
                                             MAX_DOMAIN_ATTEMPTS)


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
        appstruct = {'came_from': get_referrer(self.request)}
        if 'login' in self.request.params:
            appstruct['login'] = self.request.params['login']
        #if ('password' in self.frm.cstruct
        #    and self.frm.cstruct['password'] != ''):
        #    self.frm.cstruct['password'] = ''
        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render(appstruct=appstruct),
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
            return self.login_error(self.invalid_error)

        if user.admin_disabled:
            return self.login_error(self.disabled_error)
        elif user.locked:
            return self.login_error(self.locked_error)
        elif not self.verify_password(password, saved_hash, user):
            self.request.registry.notify(LoginFailed(self.request, user))
            # Don't just use += 1, as that is subject to race conditions
            # with concurrent updates
            user.login_attempts = UserProfile.login_attempts + 1
            self.request.db_session.flush()
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

        auth_kw = {}
        if appstruct['remember_me']:
            # default timeout for direct logins is 30 days
            auth_kw = {'max_age': 60*60*24*30}
        headers = remember(self.request, user.username, **auth_kw)
        self.request.response.headerlist.extend(headers)
        self.request.session['auth_userid'] = user.username
        # Invalidate the current token
        self.request.session.new_csrf_token()
        self.request.session.save()

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
    if return_to is None:
        referrer = get_referrer(request)
    else:
        referrer = return_to
    # Invalidate the current token
    request.session.new_csrf_token()
    request.session.save()
    request.registry.notify(LoggedOut(request, request.user))
    headers = forget(request)
    return HTTPFound(referrer, headers=headers)
