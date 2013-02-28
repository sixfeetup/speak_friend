from colander import Email, Schema, SchemaNode, SequenceSchema, String
from deform import Form


class EmailAddresses(SequenceSchema):
      email = SchemaNode(
          String(),
          title=u'Email Address',
          description=u'Add an email address to be notified.',
          validator=Email(),
      )

class UserCreationEmailNotification(Schema):
    email_addresses = EmailAddresses()

class ContactUsEmailNotification(Schema):
    email_addresses = EmailAddresses()

user_creation_email_notification_schema = UserCreationEmailNotification(
    path=u'.'.join((UserCreationEmailNotification.__module__,
                   'user_creation_email_notification_schema')),
    name=u'user_creation_email_notification',
    title=u'New User Creation: Email Notification',
    description=u'List of email addresses to notify when a new user is created.'
)

contact_us_email_notification_schema = ContactUsEmailNotification(
    path=u'.'.join((ContactUsEmailNotification.__module__,
                   'contact_us_email_notification_schema')),
    name=u'contact_us_email_notification',
    title=u'Contact Us: Email Notification',
    description=u'List of email addresses to notify when the Contact Us form is submitted.'
)
