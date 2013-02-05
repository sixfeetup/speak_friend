from unittest import TestCase

from pyramid import testing


class SFBaseCase(TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.add_settings({'site_name': "Test"})

    def tearDown(self):
        testing.tearDown()
