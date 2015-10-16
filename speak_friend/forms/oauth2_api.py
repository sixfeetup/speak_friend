from colander import SchemaNode
from colander import String
from deform import Button
from deform import Form
from deform.widget import HiddenWidget
from sixfeetup.bowab.forms.widgets import CSRFSchema


class CreateSecret(CSRFSchema):
    domain = SchemaNode(
        String(),
        widget=HiddenWidget(),
        default='',
        title=u'domain',
    )


def make_client_secret_form(request):
    schema = CreateSecret()
    secret_form = Form(
        schema.bind(request=request),
        buttons=(
            Button('submit', title='Create New Secret'),
        )
    )
    return secret_form


class ClientAuthorization(CSRFSchema):
    pass


def make_client_authorization_form(request):
    schema = ClientAuthorization()
    auth_form = Form(
        schema.bind(request=request),
        buttons=(
            Button('submit', title='Authorize Application'),
            Button('cancel', title='Deny Access'),
        )
    )
    return auth_form
