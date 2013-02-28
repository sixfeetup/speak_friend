# Views related to account management (creating, editing, deactivating)

from deform import Form, ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.renderers import render_to_response
from pyramid.view import view_defaults

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from speak_friend.forms.profiles import password_reset_request_form
from speak_friend.forms.controlpanel import password_reset_schema
from speak_friend.forms.profiles import profile_form
from speak_friend.models import DBSession
from speak_friend.models.profiles import ResetToken
from speak_friend.models.profiles import UserProfile
from speak_friend.views.controlpanel import ControlPanel


def create_profile(request):
    form = profile_form.render()
    return {
        'forms': [form],
        'rendered_form': form,
    }


def edit_profile(request):
    form = profile_form.render()
    return {
        'forms': [form],
        'rendered_form': form,
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
            captured = password_reset_request_form.validate(controls)
            self.notify(captured)
            url = self.request.route_url('home')
            return HTTPFound(location=url)
        except ValidationFailure as e:
            # the submitted values could not be validated
            html = e.render()

        return {
            'forms': [password_reset_request_form],
            'rendered_form': html,
        }

    def get(self):
        return {
            'forms': [password_reset_request_form],
            'rendered_form': password_reset_request_form.render(),
        }

    def notify(self, captured):
        query = self.session.query(UserProfile)
        query = query.filter(UserProfile.email==captured['email'])
        profile = query.first()

        mailer = get_mailer(self.request)
        user_email = '%s %s <%s>' % (profile.first_name, profile.last_name,
                                     profile.email)
        reset_token = ResetToken(profile.username)
        response = render_to_response(self.path,
                                      {'token': reset_token.token},
                                      self.request)
        self.session.merge(reset_token)
        message = Message(subject=self.subject,
                          sender=self.sender,
                          recipients=[user_email],
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
