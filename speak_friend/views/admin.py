# Views related to administrator actions. (deactivating accounts,
# changing user passwords)
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.view import view_defaults
from deform import ValidationFailure
from deform import Form

from speak_friend.forms.profiles import Domain
from speak_friend.models import DBSession
from speak_friend.models.profiles import DomainProfile


@view_defaults(route_name='create_domain')
class CreateDomain(object):
    def __init__(self, request):
        self.request = request
        self.session = DBSession()
        self.domain_form = Form(Domain(), buttons=('submit', 'cancel'))

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()

        try:
            appstruct = self.domain_form.validate(controls)  # call validate
        except ValidationFailure, e:
            return {
                'forms': [self.domain_form],
                'rendered_form': e.render(),
            }

        new_domain = DomainProfile(**appstruct)
        self.session.merge(new_domain)

        self.request.session.flash('Domain successfully created!',
                                   queue='success')
        # XXX: Update to point to domain listing page when that is finished
        url = self.request.route_url('home')
        return HTTPFound(location=url)

    def get(self, success=False):
        if success:
            return {'forms': [], 'rendered_form': '', 'success': True}
        return {
            'forms': [self.domain_form],
            'rendered_form': self.domain_form.render({}),
        }
