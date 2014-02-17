from speak_friend.models.profiles import UserProfile


def create_user(username):
    profile = UserProfile(
        username,
        'Fname',
        'Lname',
        'test@test.com',
        'asdfklhjadsfklhjasf',
        None,
        0,
        False,
    )
    return profile

class MockPasswordValidator(object):
    def __init__(self, settings={}):
        self.settings = settings

    def __call__(self, password):
        return True
