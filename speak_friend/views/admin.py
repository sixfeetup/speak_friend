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
    if 'submit' in request.POST:
        # the form has been submitted
        controls = request.POST.items()
        try:
            appstruct = domain_form.validate(controls)
        except ValidationFailure, e:
            # form failed validation
            return {
                'forms': [domain_form],
                'rendered_form': e.render(),
            }
        # form valid outcome
        session = DBSession()
        new_domain = DomainProfile(**appstruct)
        session.merge(new_domain)
        return {
            'forms': [domain_form],
            'rendered_form': domain_form.render(appstruct)
        }

    # form not yet submitted outcome
    return {
        'forms': [domain_form],
        'rendered_form': domain_form.render(),
    }
