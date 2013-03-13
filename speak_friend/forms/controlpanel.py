from colander import (
    Email, Integer, Schema, SchemaNode, SequenceSchema, String, Range)
from deform import Form


class EmailAddresses(SequenceSchema):
      email = SchemaNode(
          String(),
          title=u'Email Address',
          description=u'Add an email address to be notified.',
          validator=Email(),
      )


class EmailNotification(Schema):
    contact_us = EmailAddresses(
        description=u'List of email addresses to notify when the Contact Us form is submitted.'
    )
    user_creation = EmailAddresses(
        description=u'List of email addresses to notify when a new user is created.'
    )

MAX_DOMAIN_ATTEMPTS = 10

class Authentication(Schema):
    token_duration = SchemaNode(
        Integer(),
        default=60,
        description=u'Duration (in minutes) password reset tokens are valid for.'
    )
    max_attempts = SchemaNode(
        Integer(),
        default=MAX_DOMAIN_ATTEMPTS,
        title="Maximum login attempts",
        description="Indicate the system default number of times a user may "
                    "fail a login attempt before being disabled (must be >= 1)",
        validator=Range(min=1),
    )


class DomainDefaults(Schema):
    password_valid = SchemaNode(
        Integer(),
        default=60*24*30,
        title="Password valid",
        description="Indicate the system default time in minutes that a "
                    "password should be valid (must be >= 0)",
        validator=Range(min=0),
    )


email_notification_schema = EmailNotification(
    path=u'.'.join((EmailNotification.__module__,
                   'email_notification_schema')),
    name=u'email_notification_schema',
    title=u'Email Notification',
)


authentication_schema = Authentication(
    path=u'.'.join((Authentication.__module__,
                   'authentication_schema')),
    name=u'authentication_schema',
    title=u'Authentication',
)


domain_defaults_schema = DomainDefaults(
    path=u'.'.join((DomainDefaults.__module__,
                    'domain_defaults_schema')),
    name=u'domain_defaults_schema',
    title=u'Domain Default Values',
    description=u'Default values applied to domains without specific settings',
)
