from logging import getLogger
import transaction

from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response
from pyramid.response import Response

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from speak_friend.api import TemplateAPI
from speak_friend.forms.controlpanel import email_notification_schema
from speak_friend.models import DBSession
from speak_friend.models.profiles import UserProfile
from speak_friend.views.controlpanel import ControlPanel
from speak_friend.views.open_id import OpenIDProvider


def register_api(event):
    """Provides an 'api' variable to all templates.

    This is intended to be registered with Pyramid's 'BeforeRender'
    event so that it will be injected into the environment, without
    having to explicily add it in each view function.
    """
    if isinstance(event.rendering_val, Response):
        event['api'] = TemplateAPI(event['request'], {})
    else:
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
    # Obtain list of emails to notify from the control panel
    cp = ControlPanel(event.request)
    current = cp.saved_sections.get(email_notification_schema.name)
    if current and current.panel_values:
        recipients = current.panel_values['user_creation']
    else:
        recipients = []
    if not recipients:
        logger.info('No one to notify of account creation: %s.',
                    event.user)
        return

    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=recipients,
                      extra_headers=headers,
                      html=response.unicode_body)
    mailer.send(message)


def confirm_account_created(event):
    """Send confirmation email to user after account creation.
    """
    logger = getLogger('speak_friend.user_activity')
    path = 'speak_friend:templates/email/account_creation_confirmation.pt'
    settings = event.request.registry.settings
    subject = '%s: New user account' % settings['site_name']
    mailer = get_mailer(event.request)
    response = render_to_response(path,
                                  {'profile': event.user},
                                  event.request)
    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=[event.user.email],
                      html=response.unicode_body)
    mailer.send(message)


def handle_openid_request(event):
    if 'openid.assoc_handle' in event.request.GET and \
       event.response.status_code == 302:
        provider = OpenIDProvider(event.request)
        openid_response = provider.get()
        response_url = openid_response.headers['Location']
        event.response.headers['Location'] = response_url


def increment_failed_login_count(event):
    event.user.login_attempts += 1
    session = DBSession()
    session.add(event.user)
    transaction.commit()


def email_change_notification(event):
    if ('old_address' not in event.activity_detail and
        'new_address' not in event.activity_detail):
        return
    old = event.activity_detail['old_address']
    new = event.activity_detail['new_address']
    logger = getLogger('speak_friend.user_activity')
    logger.info('%s changed their email address' % event.user.username)
    path = 'speak_friend:templates/email/account_email_change_notification.pt'
    settings = event.request.registry.settings
    subject = '%s: Email address changed' % settings['site_name']
    mailer = get_mailer(event.request)
    response = render_to_response(path,
                                  {'profile': event.user,
                                   'old_address': old,
                                   'new_address': new,
                                  },
                                  event.request)
    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=[old, new],
                      html=response.unicode_body)
    mailer.send(message)


def email_profile_change_notification(event):
    if ('first_name' not in event.activity_detail and
        'last_name' not in event.activity_detail):
        return

    first_name = event.activity_detail.get('first_name', '')
    last_name = event.activity_detail.get('last_name', '')

    logger = getLogger('speak_friend.user_activity')
    for key, value in event.activity_detail.items():
        logger.info('%s changed their %s' % (event.user.username, key))
    path = 'speak_friend:templates/email/account_change_notification.pt'
    settings = event.request.registry.settings
    subject = '%s: Account settings changed' % settings['site_name']
    mailer = get_mailer(event.request)
    response = render_to_response(path,
                                  {'profile': event.user,
                                   'first_name': first_name,
                                   'last_name': last_name
                                  },
                                  event.request)
    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=[event.user.email],
                      html=response.unicode_body)
    mailer.send(message)
