from logging import getLogger

from openid.yadis.constants import YADIS_HEADER_NAME

from pyramid.renderers import render_to_response

from pyramid_controlpanel.views import ControlPanel

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from speak_friend.forms.controlpanel import email_notification_schema
from speak_friend.models.reports import UserActivity
from speak_friend.models.profiles import ResetToken
from speak_friend.utils import get_xrds_url


def log_activity(event):
    """Log user activity events via the logging framework.
    """
    logger = getLogger('speak_friend.user_activity')
    msg = ['User %s: %s']
    args = [event.user.username, event.activity]
    if event.activity_detail:
        msg.append('detail "%s"')
        args.append(event.activity_detail)
    if event.actor:
        msg.append('By %s')
        args.append(event.actor.username)

    logger.info(', '.join(msg), *args)


def log_user_activity(event):
    """Records all UserActivity events emitted to the user_activities
    table.
    """
    kwargs = event.__dict__
    if 'activity' not in kwargs:
        kwargs['activity'] = event.activity
    activity = UserActivity(**kwargs)
    event.request.db_session.add(activity)


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
    recipients = cp.get_value(email_notification_schema.name,
                              'user_creation', [])
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
                      recipients=[event.user.full_email],
                      html=response.unicode_body)
    mailer.send(message)


def email_change_notification(event):
    if ('old_address' not in event.activity_detail and
        'new_address' not in event.activity_detail):
        return
    same_user = event.actor == event.user

    if event.actor.is_superuser and not same_user:
        return
    old = event.activity_detail['old_address']
    new = event.activity_detail['new_address']
    logger = getLogger('speak_friend.user_activity')
    logger.info('%s changed their email address' % event.user.username)
    path = 'speak_friend:templates/email/account_email_change_notification.pt'
    settings = event.request.registry.settings
    subject = '%s: Email changed' % settings['site_name']
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

    same_user = event.actor == event.user

    if event.actor.is_superuser and not same_user:
        return

    first_name = event.activity_detail.get('first_name', '')
    last_name = event.activity_detail.get('last_name', '')

    logger = getLogger('speak_friend.user_activity')
    for key, value in event.activity_detail.items():
        logger.info('%s changed their %s' % (event.user.username, key))
    path = 'speak_friend:templates/email/account_change_notification.pt'
    settings = event.request.registry.settings
    subject = '%s: Account updated' % settings['site_name']
    mailer = get_mailer(event.request)
    response = render_to_response(path,
                                  {'profile': event.user,
                                   'first_name': first_name,
                                   'last_name': last_name
                                  },
                                  event.request)
    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=[event.user.full_email],
                      html=response.unicode_body)
    mailer.send(message)


def notify_account_locked(event):
    """Notify user when their account is locked.
    """
    logger = getLogger('speak_friend.user_activity')
    path = 'speak_friend:templates/email/account_locked_notification.pt'
    settings = event.request.registry.settings
    subject = '%s: Account disabled' % settings['site_name']
    mailer = get_mailer(event.request)
    response = render_to_response(path,
                                  {'profile': event.user},
                                  event.request)

    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=[event.user.full_email],
                      html=response.unicode_body)
    mailer.send(message)


def notify_password_request(event):
    """Send password request token to user.
    """
    logger = getLogger('speak_friend.user_activity')
    path = 'speak_friend:templates/email/password_reset_notification.pt'
    settings = event.request.registry.settings
    subject = '%s: Reset password' % settings['site_name']
    mailer = get_mailer(event.request)
    reset_token = ResetToken(event.user.username,
                             event.came_from)
    event.request.db_session.add(reset_token)
    response = render_to_response(path,
                                  {'token': reset_token.token},
                                  event.request)
    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=[event.user.full_email],
                      html=response.unicode_body)
    mailer.send(message)


def confirm_password_reset(event):
    """Send confirmation email to user after their password is reset
    if the notify_user flag is set to True (the default).
    """
    logger = getLogger('speak_friend.user_activity')
    if not event.notify_user:
        return
    path = 'speak_friend:templates/email/password_reset_confirmation.pt'
    settings = event.request.registry.settings
    subject = '%s: Password reset' % settings['site_name']
    mailer = get_mailer(event.request)
    response = render_to_response(path,
                                  {'profile': event.user},
                                  event.request)
    message = Message(subject=subject,
                      sender=settings['site_from'],
                      recipients=[event.user.full_email],
                      html=response.unicode_body)
    mailer.send(message)


def add_yadis_header(event):
    """Adds a Yadis authentication header for processing OpenID requests
    to all responses.
    """
    request = event.request
    if request is not None:
        xrds_url = get_xrds_url(request)
        request.response.headers[YADIS_HEADER_NAME] = xrds_url
