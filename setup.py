import os

from setuptools import setup, find_packages

version = '0.1'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'pyramid_tm',
    'waitress',
    'pyramid_who',
    'passlib',
    'py-bcrypt',
    'repoze.who>=2.0'
    ]

setup(
      name='speak_friend',
      version=version,
      description="An OpenID server, using LDAP as a datastore.",
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
      tests_require=requires,
      test_suite="speak_friend",
      extras_require={'test': ['mock']},
      entry_points="""\
      [paste.app_factory]
      main = speak_friend:main
      """,
      )
