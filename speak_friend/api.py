import logging

from pyramid.renderers import get_renderer
from sixfeetup.bowab.api import TemplateAPI

from speak_friend.models.profiles import DomainProfile
from speak_friend.models.reports import UserActivity

from speak_friend.utils import get_xrds_url
from speak_friend.utils import get_domain


logger = logging.getLogger(__name__)

DEFAULT_PRIMARY_COLOR = '#3A4E9F'
DEFAULT_SECONDARY_COLOR = '#929292'


class SFTemplateAPI(TemplateAPI):

    def __init__(self, request, rendering_val):
        super(SFTemplateAPI, self).__init__(request, rendering_val)
        self.init_macros()

    def init_macros(self):
        macro_names = ['footer', 'quick_links', 'nav',
                       'logo', 'head_elements', 'admin_nav', 'domain_css']
        self.macros = {}
        for mname in macro_names:
            renderer = get_renderer('templates/macros/%s#%s.pt' % (mname, mname))
            self.macros[mname] = renderer.implementation()

    @property
    def is_superuser(self):
        return self.request.user and self.request.user.is_superuser

    @property
    def xrds_url(self):
        return get_xrds_url(self.request)

    @property
    def last_checkid_domain(self):
        if not hasattr(self, '_domain'):
            user = self.request.user
            if user:
                db_session = self.request.db_session
                activity = UserActivity.last_checkid(db_session, user)
                name = activity and activity.came_from_fqdn
            else:
                came_from = self.rendering_val.get('came_from', self.request)
                name = get_domain(came_from)
            domain = None
            if name:
                domain = DomainProfile.apply_wildcard(
                    self.request.db_session, name)
            if domain:
                self._domain = domain
        logger.debug('Came from: %s', getattr(self, '_domain', None))
        return getattr(self, '_domain', None)

    @property
    def primary_color(self):
        pc = getattr(self.last_checkid_domain, 'primary_color', None)
        if not pc:
            pc = self.request.registry.settings.get(
                'speak_friend.primary_color', DEFAULT_PRIMARY_COLOR)
        return pc

    @property
    def secondary_color(self):
        sc = getattr(self.last_checkid_domain, 'secondary_color', None)
        if not sc:
            sc = self.request.registry.settings.get(
                'speak_friend.secondary_color', DEFAULT_SECONDARY_COLOR)
        return sc
