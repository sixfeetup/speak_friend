# Views related to account management (creating, editing, deactivating)

from deform import ValidationFailure
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.view import view_defaults

from speak_friend.forms.profiles import profile_form
from speak_friend.models.profiles import UserProfile


@view_defaults(route_name='create_profile')
class CreateProfile(object):
    def __init__(self, request):
        self.request = request

    def post(self):
        if self.request.method != "POST":
            return HTTPMethodNotAllowed()
        if 'submit' not in self.request.POST:
            return self.get()

        controls = self.request.POST.items()

        try:
            appstruct = profile_form.validate(controls)  # call validate
        except ValidationFailure, e:
            return {'form': e.render()}

        # the form submission succeeded, we have the data
        return {'form': None, 'appstruct': appstruct}

    def get(self):
        form = profile_form.render()
        return {'form': form}


def edit_profile(request):
    form = profile_form.render()
    return {'form': form}
