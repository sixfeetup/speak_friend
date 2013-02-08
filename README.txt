speak_friend
============

Overview
--------

A stand-alone OpenID implementation in Pyramid.


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
