# Views related to interacting with the contact form.

from deform import Form, ValidationFailure
from deform.widget import TextInputWidget
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.view import view_defaults

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message


from speak_friend.forms.contactus import make_contact_us_form
from speak_friend.forms.controlpanel import email_notification_schema
from speak_friend.views.controlpanel import ControlPanel


@view_defaults(route_name='contact_us')
class ContactUs(object):
    def __init__(self, request):
        self.request = request
        self.frm = make_contact_us_form()
        settings = request.registry.settings
        self.subject = "Contact Us Form Submission: %s" % settings['site_name']
        self.sender = settings['site_from']
        cp = ControlPanel(request)
        self.recipients = cp.get_value(email_notification_schema.name,
                                       'contact_us', [])

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST and \
           'cancel' not in self.request.POST:
            return self.get()
        try:
            controls = self.request.POST.items()
            captured = self.frm.validate(controls)
            self.notify(captured)
            if captured['came_from']:
                return HTTPFound(location=captured['came_from'])
            else:
                return HTTPFound(location=self.request.route_url('home'))
        except ValidationFailure as e:
            # the submitted values could not be validated
            html = e.render()
            if 'cancel' in self.request.POST and \
               e.cstruct['came_from']:
                return HTTPFound(location=e.cstruct['came_from'])

        return {
            'forms': [self.frm],
            'rendered_form': html,
        }

    def get(self):
        appstruct = {}
        appstruct['came_from'] = self.request.referrer
        if self.request.user:
            appstruct['contact_name'] = self.request.user.full_name
            appstruct['reply_email'] = self.request.user.email
        for field in self.frm:
            if field.name == 'contact_name' or field.name == 'reply_email':
                field.widget = TextInputWidget(template='readonly/textinput')
        rendered_form = self.frm.render(appstruct=appstruct)
        return {
            'forms': [self.frm],
            'rendered_form': rendered_form,
        }

    def notify(self, captured):
        if self.recipients:
            self.request.session.flash('Your message has been sent.',
                                       queue='success')
            mailer = get_mailer(self.request)
            reply_to = '%s <%s>' % (captured['contact_name'],
                                    captured['reply_email'])
            headers = {'Reply-To': reply_to}
            message = Message(subject=self.subject,
                              sender=self.sender,
                              recipients=self.recipients,
                              extra_headers=headers,
                              body=captured['message_body'])
            mailer.send(message)
        else:
            self.request.session.flash('No recipients have been configured.',
                                       queue='error')
