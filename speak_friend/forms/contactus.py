from colander import Email, MappingSchema, SchemaNode, String
from deform import Form
from deform.widget import HiddenWidget
from deform.widget import TextAreaWidget

from speak_friend.forms.csrf import CSRFSchema


class ContactUs(CSRFSchema):
    contact_name = SchemaNode(
        String(),
        title='Name',
    )
    reply_email = SchemaNode(
        String(),
        title='Email',
        validator=Email(),
    )
    message_body = SchemaNode(
        String(),
        title='Message',
        widget=TextAreaWidget(cols=50, rows=10),
    )
    came_from = SchemaNode(
        String(),
        widget=HiddenWidget(),
        missing='/',
        title="came_from",
    )
    title='Contact Us',
    description='Have a question or want to tell us something? Let us know.',


def make_contact_us_form(request):
    schema = ContactUs()
    contact_us_form = Form(
        schema=schema.bind(request=request),
        buttons=('submit',),
        bootstrap_form_style='form-vertical',
    )
    return contact_us_form
