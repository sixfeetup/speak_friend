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

Password Management
-------------------

This package provides a configuration plug point for specific implementations 
to determine how to manage passwords over time.  The configuration method is
called 'set_password_context' and it accepts one of four possible keyword
arguments:

* context: if provided, this must be a passlib.context.CryptContext instance
* ini_string: if provided must be a string containing configuration as written
  by the 'to_string' method of the passlib.context.CryptContext class
* ini_file: if provided, must be a string which identifies a file in .ini
  format which contains the configuration settings for a CryptContext (see the
  'to_string' method of the passlib.context.CryptContext class for a way to
  generate these settings)
* context_dict: if provided must be a dictionary of configuration values
  suitable for constructing a CryptContext object (see the to_dict method of
  the passlib.context.CryptContext class for details)

if more than one of these keywords is provided, the order above is obeyed.
CryptContext instances take precedence over ini_strings, etc.

An implementation might do something like the following:

in ``production.ini``:

.. code-block:: ini

    [app:main]
    password.context_file = /path/to/password/configuration.ini

in the package ``__init__.py``:

.. code-block:: python

    def main(global_config, **settings):
        ini_path = settings['password.context_file']
        config = Configurator(settings=settings)
        config.set_password_context(ini_path)

So long as the file identified by the path contains configuration suitable for
constructing a passlib Crypt.Context, the instance created will be found
thereafter at config.registry.password_context.

That CryptContext instance supports password encryption, verification, and
even deprecation. Given a login view with the following code, administrators
could automate the process of rolling their users from one password hashing
scheme to another automatically (example is from the passlib documentation):

.. code-block:: python

    hash = get_hash_from_user(user)
    if pass_ctx.verify(password, hash):
        if pass_ctx.needs_update(hash):
            new_hash = pass_ctx.encrypt(password)
            replace_user_hash(user, new_hash)
        do_successful_things()
    else:
        reject_user_login()

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


Overriding Assets
-----------------

There is a blank `speak_friend:static/css/custom.css` file that can be overridden by packages extending `speak_friend`.
This file is included in `base.pt`, so will be included on every page.
The following is a list of macros that can be overridden:
* `speak_friend:templates/macros/footer.pt`
* `speak_friend:templates/macros/quick_links.pt`

See http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#overriding-assets-section .
