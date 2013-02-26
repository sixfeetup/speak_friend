from logging import getLogger

from speak_friend.api import TemplateAPI


def register_api(event):
    """Provides an 'api' variable to all templates.

    This is intended to be registered with Pyramid's 'BeforeRender'
    event so that it will be injected into the environment, without
    having to explicily add it in each view function.
    """
    event['api'] = TemplateAPI(event['request'])


def log_activity(event):
    """Log user activity events via the logging framework.
    """
    logger = getLogger('speak_friend.user_activity')
    msg = ['User %s: %s']
    args = [event.username, event.activity]
    if event.activity_detail:
        msg.append('detail "%s"')
        args.append(event.activity)
    if event.actor_username:
        msg.append('By %s')
        args.append(event.actor_username)

    logger.info(', '.join(msg), *args)
