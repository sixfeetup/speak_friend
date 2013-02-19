speak_friend
============

Overview
--------

A stand-alone OpenID implementation in Pyramid.

Application Settings
--------------------

This package includes a method of storing sections of config values that should be editable through the web.
To integrate with this system, you need to define the schema for the control panel section using colander:

.. code-block:: python
    from colander import Email, Schema, SchemaNode, SequenceSchema, String

    class EmailAddresses(SequenceSchema):
          email = SchemaNode(
              String(),
              title='Email Address',
              description='Add an email address to be notified of new user creation.',
              validator=Email(),
          )

    class EmailNotification(Schema):
        email_addresses = EmailAddresses()

    email_notification_schema = EmailNotification(
        path='.'.join((EmailNotification.__module__, 'email_notification_schema')),
        name='email_notification',
        title='New User Creation: Email Notification',
        description='List of email addresses to notify when a new user is created.'
    )

Then in your application's initialization, add it via `config.add_controlpanel_section(email_notification_schema)`.
The entire list of configured sections will be available at `/control_panel`.

Extra Models
------------

If you have extra models that you would like the main `initialize_speak_friend_db` script to create,
they need to inherit from `from speak_friend.models.Base`. Then add the following to your config:

.. code-block:: ini
    speak_friend.extra_models =
        dotted.python.path.to.Model

Exception Handling
------------------

This package can integrate the pyramid_exclog and mailinglogger packages to automatically send email notifications when an exception is generated. To do so, include the following logging config:

.. code-block:: ini
   :linenos:
   # Begin logging configuration
   
   [loggers]
   keys = root, sfid, exc_logger
   
   [handlers]
   keys = console, filelog, exc_handler
   
   [formatters]
   keys = generic, exc_formatter
   
   [logger_exc_logger]
   level = ERROR
   handlers = exc_handler
   qualname = exc_logger
   
   [handler_exc_handler]
   class = mailinglogger.MailingLogger
   args = ('info@example.org', ('ERROR_DESTINATION@example.org',), 'localhost', 'Error on example.org')
   level = ERROR
   formatter = exc_formatter
   
   [formatter_exc_formatter]
   format = %(asctime)s %(message)s
   
   # End logging configuration


LDAP Configuration
-------------------
The following list of keys can be used to configure Speak Friend's LDAP connection.

speak_friend.ldap_server
   The URI for the LDAP server that Speak Friend should connect to. Required.

speak_friend.ldap_user_cn
    The user CN that Speak Friend should use when connecting. This user must be able create and edit accounts. Required.

speak_friend.ldap_password
   The password associated with the LDAP user specified above. Required.

speak_friend.ldap_base_people_dn
   The DN path where People objects are stored in LDAP. Required

speak_friend.ldap_people_filter_tmpl
   Filter used for searching LDAP People objects. Should contain the value `%(login)s`. Default: `'(uid=%(login)s)'`

speak_friend.ldap_base_group_dn
   The DN path where Group objects are stored in LDAP. Required.

speak_friend.ldap_group_filter_tmpl
   Filter used for searching LDAP groups. Should contain the value `%(userdn)s`. Default: `'(&(objectCategory=group)(member=%(userdn)s))'`

speak_friend.ldap_cache_period
   Number of seconds to cache search results. If 0, search results will not be cached. Default: 0

