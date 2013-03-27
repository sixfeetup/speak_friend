import os

from setuptools import setup, find_packages

version = '0.28'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'pyramid_tm',
    'waitress',
    'passlib',
    'py-bcrypt',
    'colander',
    'deform',
    'deform_bootstrap',
    'python-openid',
    'psycopg2',
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
    'zope.interface',
    'zope.component',
    'pyramid_exclog',
    'mailinglogger',
    'pyramid_mailer',
    'requests',
    'pyramid_beaker',
    ]

tests_require = requires + [
    'nose',
    'coverage',
]

setup(
      name='speak_friend',
      version=version,
      description="An extensible OpenID server.",
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Six Feet Up, Inc.',
      author_email='info@sixfeetup.com',
      url='http://www.sixfeetup.com',
      keywords='web pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=tests_require,
      test_suite="nose.collector",
      extras_require={'test': ['coverage', 'mock']},
      entry_points="""\
      [paste.app_factory]
      main = speak_friend:main
      [console_scripts]
      initialize_speak_friend_db = speak_friend.scripts.initializedb:main
      """,
      )
