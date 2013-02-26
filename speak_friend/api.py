# The API that should be available to templates.


from pyramid.renderers import get_renderer


class TemplateAPI(object):
    def __init__(self, request):
        self.request = request

    @property
    def settings(self):
        return self.request.registry.settings

    @property
    def macros(self):
        macro_names = ['footer', 'quick_links']
        all_macros = {}
        for mname in macro_names:
            renderer = get_renderer('templates/macros/%s#%s.pt' % (mname, mname))
            all_macros[mname] = renderer.implementation()
        return all_macros
