from logging import getLogger

from pyramid.renderers import render_to_response

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from speak_friend.api import TemplateAPI
from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile


def register_api(event):
    """Provides an 'api' variable to all templates.

    This is intended to be registered with Pyramid's 'BeforeRender'
    event so that it will be injected into the environment, without
    having to explicily add it in each view function.
    """
    event['api'] = TemplateAPI(event['request'], event.rendering_val)


def log_activity(event):
    """Log user activity events via the logging framework.
    """
    logger = getLogger('speak_friend.user_activity')
    msg = ['User %s: %s']
    args = [event.user.username, event.activity]
    if event.activity_detail:
        msg.append('detail "%s"')
        args.append(event.activity)
    if event.actor:
        msg.append('By %s')
        args.append(event.actor.username)

    logger.info(', '.join(msg), *args)


def notify_account_created(event):
    """Notify site admins when an account is created.
    """
    logger = getLogger('speak_friend.user_activity')
    path = 'speak_friend:templates/email/account_creation_notification.pt'
    settings = event.request.registry.settings
    subject = '%s: New user created' % settings['site_name']
    mailer = get_mailer(event.request)
    headers = {'Reply-To': event.user.full_email}
    response = render_to_response(path,
                                  {'profile': event.user},
                                  event.request)
    session = DBSession()
    query = session.query(UserProfile)
    query = query.filter(UserProfile.is_superuser==True)
    superusers = [
        user.full_email
        for user in query.all()
    ]
    if not superusers:
        logger.info('No super-users to notify of account creation: %s.',
                    event.user)
        return

    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=superusers,
                      extra_headers=headers,
                      html=response.unicode_body)
    mailer.send(message)
