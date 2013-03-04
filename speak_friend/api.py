# The API that should be available to templates.
import datetime

from pyramid.renderers import get_renderer


class TemplateAPI(object):
    def __init__(self, request, rendering_val):
        self.request = request
        self.init_macros()
        self.init_forms(rendering_val)

    @property
    def settings(self):
        return self.request.registry.settings

    @property
    def utc_now(self):
        # totally naive as to timezone.
        return datetime.datetime.utcnow()

    def init_macros(self):
        macro_names = ['footer', 'quick_links', 'nav', 'logo']
        self.macros = {}
        for mname in macro_names:
            renderer = get_renderer('templates/macros/%s#%s.pt' % (mname, mname))
            self.macros[mname] = renderer.implementation()

    def init_forms(self, rendering_val):
        # Initialize any necessary form resources
        self.css_resources = []
        self.js_resources = []
        for form in rendering_val.get('forms', []):
            resources = form.get_widget_resources()
            # XXX: Is the path always going to have this prefix?
            self.css_resources.extend([
                'deform:static/%s' % css_path
                for css_path in resources['css']
            ])
            self.js_resources.extend([
                'deform:static/%s' % js_path
                for js_path in resources['js']
            ])
