# Views related to account management (creating, editing, deactivating)
from speak_friend.forms.profiles import profile_form


def create_profile(request):
    form = profile_form.render()
    return {
        'forms': [form],
        'rendered_form': form,
    }


def edit_profile(request):
    form = profile_form.render()
    return {
        'forms': [form],
        'rendered_form': form,
    }
