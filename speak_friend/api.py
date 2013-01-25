# The API that should be available to templates.


from pyramid.threadlocal import get_current_registry


class TemplateAPI(object):
    def __init__(self):
        pass

    @property
    def settings(self):
        return get_current_registry().settings
