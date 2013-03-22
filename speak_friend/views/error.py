from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.security import authenticated_userid

import transaction

from speak_friend.views.accounts import LoginView

def notfound(request):
    return render_to_response("speak_friend:templates/404_template.pt",
                              {},
                              request=request)


def notallowed(request):
    auth_userid = authenticated_userid(request)
    if auth_userid is None:
        login = LoginView(request)
        if request.method == 'POST':
            # Process the login form and redirect
            view_method = login.post
        else:
            # User is not logged in, render the login form
            view_method = login.get
        response = view_method()
        # We need to commit the transaction, so that details about
        # the forbidden view can be written to the database
        transaction.commit()
        if isinstance(response, Response):
            return response
        else:
            return render_to_response("speak_friend:templates/login.pt",
                                      response,
                                      request=request)
    else:
        # If the user is logged in, they don't have permission
        return render_to_response("speak_friend:templates/403_template.pt",
                                  {},
                                  request=request)
