from colander import Email, MappingSchema, SchemaNode, String
from deform import Form
from deform.widget import CheckedInputWidget


class ContactUs(MappingSchema):
    contact_name = SchemaNode(String())
    reply_email = SchemaNode(
        String(),
        validator=Email(),
        widget=CheckedInputWidget(),
    )


contact_us_form = Form(ContactUs(), buttons=('submit', 'cancel'))
