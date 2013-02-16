# Views related to administrator actions. (deactivating accounts,
# changing user passwords)
from speak_friend.forms.profiles import domain_form


def create_domain(request):
    form = domain_form.render()
    return {'form': form}