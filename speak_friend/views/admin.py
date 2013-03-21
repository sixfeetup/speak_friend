# Views related to administrator actions. (deactivating accounts,
# changing user passwords)
import transaction

from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_defaults
from deform import ValidationFailure
from deform import Form
from sqlalchemy import select, func, desc

from speak_friend.forms.profiles import Domain
from speak_friend.forms.profiles import EditDomain as EditDomainSchema
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
                'delete_url': 'http://uw.edu',
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
        self.domain_form = make_edit_domain_form(request)
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

        if self.target_domain.password_valid != appstruct['password_valid']:
            self.target_domain.password_valid = appstruct['password_valid']
        self.session.flush()
        # Have to manually commit here, as HTTPFound will cause
        # a transaction abort
        transaction.commit()
        self.request.db_session.add(self.target_domain)

        self.request.session.flash('Domain successfully modified!',
                                   queue='success')
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
