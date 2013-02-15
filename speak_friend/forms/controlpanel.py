from colander import Email, Schema, SchemaNode, SequenceSchema, String
from deform import Form


class EmailAddresses(SequenceSchema):
      email = SchemaNode(
          String(),
          title='Email Address',
          description='Add an email address to be notified of new user creation.',
          validator=Email(),
      )

class UserCreationEmailNotification(Schema):
    email_addresses = EmailAddresses()

user_creation_email_notification_schema = UserCreationEmailNotification(
    path='.'.join((UserCreationEmailNotification.__module__,
                   'user_creation_email_notification_schema')),
    name='user_creation_email_notification',
    title='New User Creation: Email Notification',
    description='List of email addresses to notify when a new user is created.'
)
