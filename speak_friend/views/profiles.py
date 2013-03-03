# Views related to account management (creating, editing, deactivating)

from deform import ValidationFailure
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.view import view_defaults

from speak_friend.forms.profiles import profile_form
from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile


@view_defaults(route_name='create_profile')
class CreateProfile(object):
    def __init__(self, request):
        self.request = request
        self.session = DBSession()

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

        # XXX We can't just pass the password in here; we need to pull it from
        # the appstruct and run it through the password hasher. XXX XXX

        profile = UserProfile(appstruct['username'],
                              appstruct['first_name'],
                              appstruct['last_name'],
                              appstruct['email'],
                              appstruct['password'],
                              appstruct['password'],
                              0,
                              False
        )

        self.session.add(profile)
        # TODO This should really return a confirmation page.
        return {'form': None, 'appstruct': appstruct}

    def get(self):
        form = profile_form.render()
        return {'form': form}


def edit_profile(request):
    form = profile_form.render()
    return {'form': form}
