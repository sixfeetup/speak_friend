# Views related to account management (creating, editing, deactivating)

from pyramid.response import Response


def create_account(request):
    return {}


def edit_account(request):
    return Response("Edit Account")
