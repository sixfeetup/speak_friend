# Views related to interacting with the contact form.

from deform import Form, ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.view import view_defaults

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message


from speak_friend.forms.contactus import contact_us_form
from speak_friend.views.controlpanel import ControlPanel
from speak_friend.forms.controlpanel import contact_us_email_notification_schema


# FIXME: attach appropriate permissions
@view_defaults(route_name='contact_us')
class ContactUs(object):
    def __init__(self, request):
        self.request = request
        settings = request.registry.settings
        self.subject = "Contact Us Form Submission: %s" % settings['site_name']
        self.sender = settings['site_from']
        cp = ControlPanel(request)

        current = cp.saved_sections.get(contact_us_email_notification_schema.name)
        if current and current.panel_values:
            self.recipients = current.panel_values['email_addresses']
        else:
            self.recipients = []

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()
        try:
            controls = self.request.POST.items()
            captured = contact_us_form.validate(controls)
            self.notify(captured)
            url = self.request.route_url('home')
            return HTTPFound(location=url)
        except ValidationFailure as e:
            # the submitted values could not be validated
            html = e.render()

        return {
            'forms': [contact_us_form],
            'rendered_form': html,
        }

    def get(self):
        return {
            'forms': [contact_us_form],
            'rendered_form': contact_us_form.render(),
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
                              recipients=tuple(self.recipients),
                              extra_headers=headers,
                              body=captured['message_body'])
            mailer.send(message)
        else:
            self.request.session.flash('No recipients have been configured.',
                                       queue='error')
