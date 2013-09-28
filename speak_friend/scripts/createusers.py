from cStringIO import StringIO
import csv
import logging
import os
import sys

from pwgen import pwgen

from sixfeetup.bowab.scripts.common import bootstrap_script
from speak_friend.models.profiles import UserProfile


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage %s <config_uri> <num_users>\n'
          '(example: "%s development.ini 4000")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 3:
        usage(argv)
    config_uri = argv[1]
    try:
        num_users = int(argv[2])
    except ValueError:
        usage(argv)
    env = bootstrap_script(config_uri)
    db_session = env['registry']['bowab.db_session']

    logger = logging.getLogger('speak_friend.createusers')

    pass_ctx = env['registry'].password_context
    user_num = 1
    buf = StringIO()
    cols = ['username', 'first_name', 'last_name', 'email', 'password_hash',
            'password_salt', 'login_attempts', 'admin_disabled',
            'is_superuser']
    csv_file = csv.DictWriter(buf, cols, delimiter='\t', lineterminator='\n')
    logger.info("Beginning to create %d users,", num_users)
    cxn = db_session.connection()
    cur = cxn.connection.cursor()
    user_passwords = {}
    while user_num <= num_users:
        first_name = u'Test'
        last_name = pwgen(num_pw=1, pw_length=10, no_numerals=True,
                          no_symbols=True)
        username = u'%s.%s' % (first_name, last_name)
        password = pwgen(num_pw=1, pw_length=20)
        user_passwords[username] = password
        csv_file.writerow(dict(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=u'%s@example.com' % username,
            password_hash=pass_ctx.encrypt(password),
            password_salt='',
            login_attempts=0,
            admin_disabled=False,
            is_superuser=False,
        ))
        logger.info("Created user %s, %04d/%04d.",
                    username, user_num, num_users)
        user_num += 1

    logger.info("Committing...")
    tname = '%s.%s' % (UserProfile.__table__.schema,
                       UserProfile.__table__.name)
    buf.seek(0)
    cur.copy_from(buf, tname, columns=cols)
    cxn.connection.commit()

    for uname, pw in user_passwords.items():
        print uname, pw
