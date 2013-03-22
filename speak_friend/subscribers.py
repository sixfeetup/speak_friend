from datetime import datetime, timedelta
from logging import getLogger

from psycopg2.tz import FixedOffsetTimezone

from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response
from pyramid.response import Response

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from speak_friend.api import TemplateAPI
from speak_friend.forms.controlpanel import MAX_PASSWORD_VALID
from speak_friend.forms.controlpanel import email_notification_schema
from speak_friend.models.reports import UserActivity
from speak_friend.models.profiles import DomainProfile
from speak_friend.models.profiles import ResetToken
from speak_friend.models.profiles import UserProfile
from speak_friend.utils import get_domain
from speak_friend.utils import get_referrer
from speak_friend.views.accounts import logout
from speak_friend.views.controlpanel import ControlPanel
from speak_friend.views.open_id import OpenIDProvider


def register_api(event):
    """Provides an 'api' variable to all templates.

    This is intended to be registered with Pyramid's 'BeforeRender'
    event so that it will be injected into the environment, without
    having to explicily add it in each view function.
    """
    if isinstance(event.rendering_val, Response) or \
       isinstance(event.rendering_val, basestring):
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


def log_user_activity(event):
    """Records all UserActivity events emitted to the user_activities
    table.
    """
    activity = UserActivity(**event.__dict__)
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
                      recipients=[event.user.full_email],
                      html=response.unicode_body)
    mailer.send(message)


def handle_openid_request(event):
    if 'openid.mode' in event.request.GET or \
       'openid.mode' in event.request.POST:
        provider = OpenIDProvider(event.request)
        if event.request.method == 'POST':
            openid_response = provider.post()
        else:
            openid_response = provider.get()
        if event.response.status_code == 302:
            response_url = openid_response.headers['Location']
            event.response.headers['Location'] = response_url
        if not isinstance(openid_response, HTTPFound):
            event.response.body = openid_response


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


def check_password_timeout(event):
    """Verify the last login timestamp is still valid.
    """
    if not event.request.user:
        return

    domain_name = get_domain(event.request)
    domain = event.request.db_session.query(DomainProfile).get(domain_name)
    if domain:
        pw_valid = timedelta(minutes=domain.get_password_valid())
    else:
        pw_valid = timedelta(minutes=MAX_PASSWORD_VALID)

    now = datetime.utcnow()
    utc_now = now.replace(tzinfo=FixedOffsetTimezone(offset=0))
    last_login = event.request.user.last_login(event.request.db_session)
    if last_login and last_login.activity_ts + pw_valid < utc_now:
        response = logout(event.request, get_referrer(event.request))
        headers = [
            (name, val)
            for name, val in response.headerlist
            if name.lower() == 'set-cookie'
        ]
        event.response.headerlist.extend(headers)


def notify_password_request(event):
    """Send password request token to user.
    """
    logger = getLogger('speak_friend.user_activity')
    path = 'speak_friend:templates/email/password_reset_notification.pt'
    settings = event.request.registry.settings
    subject = '%s: Reset password' % settings['site_name']
    mailer = get_mailer(event.request)
    reset_token = ResetToken(event.user.username,
                             event.activity_detail['came_from'])
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
    """Send confirmation email to user after their password is reset.
    """
    logger = getLogger('speak_friend.user_activity')
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
