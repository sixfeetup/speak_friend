# Views related to account management (creating, editing, deactivating)


from speak_friend.forms.profiles import profile_form
from speak_friend.forms.profiles import domain_form


def create_profile(request):
    form = profile_form.render()
    return {'form': form}


def edit_profile(request):
    form = profile_form.render()
    return {'form': form}


def add_domain(request):
    form = domain_form.render()
    return {'form': form}
