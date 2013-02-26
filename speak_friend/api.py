# The API that should be available to templates.


from pyramid.renderers import get_renderer
from pyramid.threadlocal import get_current_registry


class TemplateAPI(object):
    def __init__(self):
        pass

    @property
    def settings(self):
        return get_current_registry().settings

    @property
    def macros(self):
        macro_names = ['footer', 'quick_links']
        all_macros = {}
        for mname in macro_names:
            renderer = get_renderer('templates/macros/%s#%s.pt' % (mname, mname))
            all_macros[mname] = renderer.implementation()
        return all_macros
