from colander import Bool, Email, MappingSchema, SchemaNode, String, Integer
from deform import Form
from deform.widget import CheckedInputWidget, CheckedPasswordWidget


class Profile(MappingSchema):
    username = SchemaNode(String())
    first_name = SchemaNode(String())
    last_name = SchemaNode(String())
    email = SchemaNode(String(),
                       validator=Email(),
                       widget=CheckedInputWidget())
    password = SchemaNode(String(),
                          widget=CheckedPasswordWidget())
    agree_to_policy = SchemaNode(Bool(),
                                 title='I agree to the usage policy.')
    captcha = SchemaNode(String())


profile_form = Form(Profile(), buttons=('submit', 'cancel'))


class Domain(MappingSchema):
    name = SchemaNode(String())
    password_valid = SchemaNode(Integer())
    max_attempts = SchemaNode(Integer())


domain_form = Form(Domain(), buttons=('submit', 'cancel'))
