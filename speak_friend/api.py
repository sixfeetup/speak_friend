from pyramid.renderers import get_renderer
from sixfeetup.bowab.api import TemplateAPI

from speak_friend.utils import get_xrds_url


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
