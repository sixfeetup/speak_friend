# Views related to administrator actions. (deactivating accounts,
# changing user passwords)
from deform import Form
from deform import ValidationFailure

from speak_friend.models import DBSession
from speak_friend.forms.profiles import Domain
from speak_friend.models.profiles import DomainProfile


def create_domain(request):
    domain_schema = Domain()
    domain_form = Form(domain_schema, buttons=('submit', 'cancel', ))
    js_resources = ['deform:static/scripts/deform.js',]
    css_resources = ['deform:static/css/form.css',]
    if 'submit' in request.POST:
        # the form has been submitted
        controls = request.POST.items()
        try:
            appstruct = domain_form.validate(controls)
        except ValidationFailure, e:
            # form failed validation
            return {'form': e.render(),
                    'js_resources': js_resources,
                    'css_resources': css_resources}
        # form valid outcome
        session = DBSession()
        new_domain = DomainProfile(**appstruct)
        session.merge(new_domain)
        return {'form': domain_form.render(appstruct),
                'js_resources': js_resources,
                'css_resources': css_resources}

    # form not yet submitted outcome
    return {'form': domain_form.render(),
            'js_resources': js_resources,
            'css_resources': css_resources}
