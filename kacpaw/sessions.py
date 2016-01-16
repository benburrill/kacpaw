import requests

from kacpaw.content import User
from kacpaw.utils import kaurl

class KASession(requests.Session): # todo: attempt to use the OAuth flow again (in a different class)
    """A session that is logged into KA"""
    def __init__(self, username, password, user_agent="Ben-Burrill-Bot Python"):
        """
        To log into KA, you need a username and password.
        ``username`` is your KA username although I think it can also be your email.
        ``password`` is your KA password.  I don't think the password you use with your email works.
        You can also provide a user_agent to use for all requests.
        """
        super().__init__()
        self.headers["User-Agent"] = user_agent

        self.login(username, password)

    def login(self, username, password):
        self.get(kaurl("login")).raise_for_status()

        # I'm a little unclear about the nature of KA fkeys, but you can
        # recieve them by going to /login and they seem to persist throughout
        # the session - at least I hope so!
        fkey = self.headers["x-ka-fkey"] = self.cookies["fkey"]
        self.post(kaurl("login"), data={
            "identifier": username,
            "password": password,
            "fkey": fkey
        }).raise_for_status()

        self.user = User(self.user_id)

    # note that although there is a user_id property which may sound like the
    # id from Content subclasses, KASessions are not in any way related to
    # content.  There is no id property for one, and sessions cannot be tested
    # for equality, hashed, etc...
    @property
    def user_id(self):
        """
        Gets the user id of the logged in user
        """
        # api/v1/user gives info on the authorized user by default
        resp = self.get(kaurl("api/v1/user"))
        resp.raise_for_status()
        return resp.json()["kaid"]