# Views related to administrator actions. (deactivating accounts,
# changing user passwords)
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.renderers import render_to_response
from pyramid.view import view_defaults

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from deform import ValidationFailure
from sqlalchemy import select, func, desc
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from speak_friend.forms.profiles import make_domain_form
from speak_friend.forms.profiles import make_user_search_form
from speak_friend.forms.profiles import make_disable_user_form
from speak_friend.models import DBSession
from speak_friend.models.profiles import DomainProfile
from speak_friend.models.profiles import ResetToken
from speak_friend.models.profiles import UserProfile
from speak_friend.views.controlpanel import ControlPanel
from speak_friend.utils import get_domain, get_referrer


@view_defaults(route_name="list_domains")
class ListDomains(object):
    def __init__(self, request):
        self.request = request
        self.cp = ControlPanel(request)

    def get(self):
        domain_records = self.request.db_session.query(DomainProfile)
        domain_records = domain_records.order_by(DomainProfile.name).all()
        domains = []
        for domain in domain_records:
            domain_dict = {
                'name': domain.name,
                'password_valid': domain.get_password_valid(self.cp),
                'edit_url': self.request.route_url('edit_domain',
                                                   domain_name=domain.name),
            }
            domains.append(domain_dict)
        create_url = self.request.route_url('create_domain')
        return {
            'domains': domains,
            'create_url': create_url,
        }


@view_defaults(route_name='create_domain')
class CreateDomain(object):
    def __init__(self, request):
        self.request = request
        self.domain_form = make_domain_form(request)

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
        self.request.db_session.merge(new_domain)

        self.request.session.flash('Domain successfully created!',
                                   queue='success')
        url = self.request.route_url('list_domains')
        return HTTPFound(location=url)

    def get(self, success=False):
        if success:
            return {'forms': [], 'rendered_form': '', 'success': True}
        return {
            'forms': [self.domain_form],
            'rendered_form': self.domain_form.render({}),
        }


@view_defaults(route_name="edit_domain")
class EditDomain(object):
    def __init__(self, request):
        self.request = request
        self.target_domainname = request.matchdict['domain_name']
        query = self.request.db_session.query(DomainProfile)
        self.target_domain = query.get(self.target_domainname)
        if self.target_domain is None:
            raise HTTPNotFound()
        self.domain_form = make_domain_form(request,
                                            domain=self.target_domain)
        self.return_url = self.request.route_url('list_domains')

    def get(self):
        appstruct = self.target_domain.make_appstruct()
        data = {
            'forms': [self.domain_form],
            'rendered_form': self.domain_form.render(appstruct),
            'target_domainname': self.target_domainname
        }
        return data

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'cancel' in self.request.POST:
            self.request.session.flash('Domain edit cancelled',
                                       queue='success')
            return HTTPFound(location=self.return_url)
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()

        try:
            appstruct = self.domain_form.validate(controls)  # call validate
        except ValidationFailure, e:
            return {
                'forms': [self.domain_form],
                'rendered_form': e.render(),
                'target_domainname': self.target_domainname
            }

        if self.target_domain.name != appstruct['name']:
            self.target_domain.name = appstruct['name']
        if self.target_domain.password_valid != appstruct['password_valid']:
            self.target_domain.password_valid = appstruct['password_valid']
        self.request.db_session.add(self.target_domain)

        self.request.session.flash('Domain successfully modified!',
                                   queue='success')
        return HTTPFound(location=self.return_url)


@view_defaults(route_name='delete_domain')
class DeleteDomain(object):
    def __init__(self, request):
        self.request = request
        self.return_url = self.request.route_url('list_domains')

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            # this was submitted without submitting the form, no good
            msg = 'Unable to delete domains except by form submission'
            return HTTPBadRequest(msg)

        target_domainname = self.request.POST.get('name', None)
        domain_found = False
        msg = 'Unable to delete %s, '
        msg_queue = 'error'
        try:
            query = self.request.db_session.query(DomainProfile).filter(
                DomainProfile.name==target_domainname)
            target_domain = query.one()
            domain_found = True
        except MultipleResultsFound:
            msg += 'the name does not uniquely identify a domain record.'
        except NoResultFound:
            msg += 'the domain record does not exist.'

        if domain_found:
            self.request.db_session.delete(target_domain)
            msg = 'The domain %s was successfully deleted'
            msg_queue = 'success'

        self.request.session.flash(msg % target_domainname, queue=msg_queue)
        return HTTPFound(location=self.return_url)


@view_defaults(route_name='user_search')
class UserSearch(object):
    def __init__(self, request):
        self.request = request
        self.frm = make_user_search_form()

    def get(self):
        if 'query' in self.request.GET:
            return self.run_search()
        query = self.request.db_session.query(UserProfile)
        query = query.order_by(UserProfile.username.desc())

        results = query.all()
        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render(),
            'results': results,
            'ran_search': False
        }

    def run_search(self):
        results = []
        ran_search = False

        try:
            controls = self.request.GET.items()
            appstruct = self.frm.validate(controls)
        except ValidationFailure, e:
            return {
                'forms': [self.frm],
                'rendered_form': e.render(),
                'results': results,
                'ran_search': ran_search,
            }
        #XXX: always default to treating the query as a prefix query??
        tsquery = func.to_tsquery("%s:*" % appstruct['query'])
        # build the shared query bit
        query_select = select([tsquery.label('query')]).cte('query_select')
        # build the ordered-by clause, using the shared query
        orderby = func.ts_rank_cd(UserProfile.searchable_text,
                                  select([query_select.c.query]))

        res = self.request.db_session.query(UserProfile)
        res = res.filter(
            UserProfile.searchable_text.op('@@')(
                select([query_select.c.query])))
        res = res.order_by(desc(orderby))

        results = res.all()
        ran_search = True
        return {
            'forms': [self.frm],
            'rendered_form': self.frm.render(),
            'results': results,
            'ran_search': ran_search,
        }


@view_defaults(route_name='request_user_password')
class RequestUserPassword(object):
    def __init__(self, request):
        self.request = request
        self.session = DBSession()
        self.path = 'speak_friend:templates/email/admin_password_reset_notification.pt'
        settings = request.registry.settings
        self.subject = "%s: Reset password" % settings['site_name']
        self.sender = settings['site_from']
        self.target_username = request.matchdict['username']

    def get_target_user(self, username):
        query = self.session.query(UserProfile)
        query = query.filter(UserProfile.username==username)
        user = query.first()
        return user

    def get(self):
        target_user = self.get_target_user(self.target_username)
        self.notify(target_user)

        return HTTPFound(location=get_referrer(self.request))

    def notify(self, user):

        mailer = get_mailer(self.request)
        came_from = get_domain(self.request)
        reset_token = ResetToken(user.username, came_from)
        response = render_to_response(self.path,
                                      {'token': reset_token.token},
                                      self.request)
        self.session.add(reset_token)
        message = Message(subject=self.subject,
                          sender=self.sender,
                          recipients=[user.full_email],
                          html=response.unicode_body)
        mailer.send(message)
        flash_msg = "A link to reset %s's password has been sent to their email."
        self.request.session.flash(flash_msg % user.username, queue='success')

@view_defaults(route_name='disable_user')
class DisableUser(object):
    def __init__(self, request):
        self.request = request
        self.session = DBSession()
        self.target_username = request.matchdict['username']
        self.form = make_disable_user_form()
        self.form.action = request.route_url('disable_user',
                                             username=self.target_username)

    def get_target_user(self, username):
        user_query = self.session.query(UserProfile)
        user_query = user_query.filter(UserProfile.username==self.target_username)
        user = user_query.first()
        return user

    def get(self):
        appstruct = {'username': self.target_username}
        rendered = self.form.render(appstruct)
        user = self.get_target_user(self.target_username)
        action = {True: 'enable', False: 'disable'}[user.admin_disabled]
        return {
            'forms': [self.form],
            'rendered_form': rendered,
            'username': self.target_username,
            'action': action,
        }

    def post(self):
        if 'submit' not in self.request.POST:
            return self.get()
        controls = self.request.POST.items()
        try:
            appstruct = self.form.validate(controls)
        except ValidationFailure,e:
            data = {
                'forms': [self.form],
                'rendered_form': e.render(),
                'username': self.target_username,
            }
            return data

        user = self.get_target_user(self.target_username)

        user.admin_disabled = not user.admin_disabled

        action = {True: 'disabled', False: 'enabled'}[user.admin_disabled]

        self.session.add(user)
        return {
            'status_msg': '%s was %s.' % (self.target_username, action),
            'action': action,
        }
