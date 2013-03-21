# Views related to administrator actions. (deactivating accounts,
# changing user passwords)
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_defaults
from deform import ValidationFailure
from sqlalchemy import select, func, desc
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from speak_friend.forms.profiles import make_domain_form
from speak_friend.forms.profiles import make_user_search_form
from speak_friend.models.profiles import DomainProfile
from speak_friend.models.profiles import UserProfile
from speak_friend.views.controlpanel import ControlPanel


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

    def get(self):
        form = make_user_search_form()
        query = self.request.db_session.query(UserProfile)
        query = query.order_by(UserProfile.username.desc())

        results = query.all()
        return {
            'forms': [form],
            'rendered_form': form.render(),
            'results': results,
            'ran_search': False
        }

    def post(self):
        results = []
        ran_search = False
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'query' not in self.request.POST:
            return self.get()

        myform = make_user_search_form(self.request)
        try:
            controls = self.request.POST.items()
            appstruct = myform.validate(controls)
        except ValidationFailure, e:
            return {
                'forms': [myform],
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
            'forms': [myform],
            'rendered_form': myform.render(),
            'results': results,
            'ran_search': ran_search,
        }
