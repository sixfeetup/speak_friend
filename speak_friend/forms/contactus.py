from colander import Email, MappingSchema, SchemaNode, String
from deform import Form
from deform.widget import TextAreaWidget


class ContactUs(MappingSchema):
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
    title='Contact Us',
    description='Have a question or want to tell us something? Let us know.',


contact_us_form = Form(
    ContactUs(),
    buttons=('submit',),
)
