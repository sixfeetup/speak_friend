# Views related to administrator actions. (deactivating accounts,
# changing user passwords)
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.view import view_defaults
from deform import ValidationFailure
from deform import Form
from sqlalchemy import select, func, desc

from speak_friend.forms.profiles import Domain
from speak_friend.forms.profiles import make_user_search_form
from speak_friend.models import DBSession
from speak_friend.models.profiles import DomainProfile
from speak_friend.models.profiles import UserProfile


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


@view_defaults(route_name='user_search')
class UserSearch(object):
    def __init__(self, request):
        self.request = request
        self.session = DBSession()

    def get(self):
        form = make_user_search_form()
        query = self.session.query(UserProfile)
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

        res = self.session.query(UserProfile)
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
