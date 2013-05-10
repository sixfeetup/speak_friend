speak_friend
============

Overview
--------

A stand-alone OpenID implementation in Pyramid.

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

Password Validation
-------------------

This package provides a pluggable system for validating the format of user
passwords. The package provides a default password validator with configurable
settings. This default validator can be replaced as well, allowing for maximal
flexibility. The validator may be found as an attribute of the current
registry: `config.registry.password_validator`. It is a callable, and calling
it will result either in `None` (if a password is valid) or a string
containing readable error messages indicating which validation rule has been
viiolated. Assuming that minimum length is set to 6, the following would
result:

.. code-block:: python

    validator = config.registry.password_validator
    password = 'secret'
    result = validator(password)
    result is None
    # True
    bad_password = 'short'
    result = validator(bad_password)
    print result
    # 'Password must be longer than 6 characters.'

Default Validator
+++++++++++++++++

The default validation is provided by the
`speak_friend.passwords.PasswordValidator` class. This class has configuration
settings that can be set via the `.ini` file. The following settings are
supported:

**speak_friend.password.min_length**
  Require a minimum length for passwords. *Default*: None

**speak_friend.password.max_length**
  Require a maximum length for passwords. *Default*: None

**speak_friend.password.min_lower**
  Require a minimum number of lower-case alphabetic characters. *Default*: 0

**speak_friend.password.min_upper**
  Require a minimum number of upper-case alphabetic characters. *Default*: 0

**speak_friend.password.min_numeric**
  Require a minimum number of numbers. *Default*: 0

**speak_friend.password.min_special**
  Require a minimum number of *special* characters. *Special* characters are
  defined by the Python regular expression `[\W|_]`. *Default*: 0

**speak_friend.password.disallowed**
  If any characters should be forbidden from use in passwords, they may be set
  with this setting. The forbidden characters should be written in a single 
  string all run together with no spaces (unless the space character itself
  is forbidden). For example, a value for this settings of `)($%'"` would 
  result in the characters `)`, `(`, `$`, `%`, `'` and `"` being disallowed in
  passwords.

Overriding the Default Validator
++++++++++++++++++++++++++++++++

The password validator is initialized by a call to the configuration directive
`set_password_validator`. By default, this directive is called without an
argument and sets the default password validator.

Should a specific implementation project require validation not provided by
the default validator, the directive may be called with a single positional
argument. 

This argument must be a callable class. The `__call__` method must accept a
password as the sole argument and return `None` if the password passes
validation. If the password fails validation, the method must return a string
describing the reason for failure. This string will be used as a message to
the end-user and should be formatted appropriately.

The `__init__` method of the class will be passed `config.registry.settings`
as it's only positional argument. The validator need not use these settings,
but the `__init__` method must accept them.

For example, if the following class exists in `my_project.password`:

.. code-block:: python

    class NoBValidator(object):
        def __init__(self, settings):
            pass
        
        def __call__(self, password):
            if 'B' not in password:
                return None
            else:
                return 'Password may not contain the letter "B"'

This validator could be used in `my_project.__init__.py` like so:

.. code-block:: python

    from pyramid.config import Configurator
    
    from my_project.password import NoBValidator
    
    def main(global_config, **settings):
        config = Configurator(settings=settings)
        
        # registers the 'set_password_validator' directive
        # and sets the default validator
        config.include('speak_friend')
        
        # prevent config conflicts as we replace the default validator
        config.commit()
        
        # replace the default with our own validator
        config.set_password_validator(NoBValidator)

After this, the validator will no longer accept any password containing the
uppercase letter 'B'.


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

Sessions
--------

By default, `speak_friend` uses `Beaker` for session management. This means that you need to configure it in your `paster.ini`:

http://docs.pylonsproject.org/projects/pyramid_beaker/en/latest/index.html#session-management

The recommended values are:

.. code-block:: ini
    :linenos:
    session.type = ext:database
    session.url = postgresql+psycopg2://dbuser:dbpass@dbhost/dbname
    session.lock_dir = %(here)s/sessions/lock
    session.key = speak_friend
    session.secret = SOME_SECRET
    session.cookie_on_exception = true
    session.secure = true


Cross-Site Request Forgery
--------------------------

`speak_friend` uses Pyramid's built-in support for mitigating CSRF attacks by storing a token in the user's session.
This token is included in forms, and the submitted value must match the current value in the session.
If not, the request will be rejected.
