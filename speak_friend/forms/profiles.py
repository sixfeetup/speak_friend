from colander import Bool, Email, MappingSchema, SchemaNode, String
from deform import Form


class Profile(MappingSchema):
    username = SchemaNode(String())
    first_name = SchemaNode(String())
    last_name = SchemaNode(String())
    email = SchemaNode(String(), validator=Email())
    confirm_email = SchemaNode(String())
    password = SchemaNode(String())
    confirm_password = SchemaNode(String())
    agree_to_policy = SchemaNode(Bool())


profile_form = Form(Profile(), buttons=('submit', 'cancel'))
