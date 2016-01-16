import requests
import kacpaw.content_abcs as abcs
from kacpaw.utils import kaurl, update_dict_path


class User(abcs.Editable):
    """
    A user on KA.  

    Note on deletion: Users are technically deletable, but I don't want to
    implement account deletion.  There are no use cases I can think of and
    it's not something that you would want to do on accident.  If you want to
    implement account deletion, subclass this like this::
        class DeletableUser(Deletable, User):
            ...
    
    and define api_delete.
    """

    get_user = kaurl("api/internal/user/profile")
    api_get = property((get_user + "?kaid={.id}").format)

    # todo: I'm still trying to get user profile editing to work.  It seems that giving the entire metadata object causes errors.
    api_edit = kaurl("api/internal/user/profile")
    api_edit_method = "POST"

    meta_path_map = {
        "bio": ["bio"],
        "name": ["nickname"],
        "username": ["username"]
    }

    def __init__(self, ka_id):
        self.ka_id = ka_id

    @classmethod
    def _from_identifier(cls, identifier_kind, identifier):
        """Gets a user by an arbitrary identifier"""
        resp = requests.get(cls.get_user, params={
            identifier_kind: identifier
        })
        resp.raise_for_status()

        return cls(resp.json()["kaid"])

    @classmethod
    def from_username(cls, username):
        """Gets a user by their username"""
        return cls._from_identifier("username", username)

    @classmethod
    def from_email(cls, email):
        """Gets a user by thier email"""
        return cls._from_identifier("email", email)

    @property
    def id(self):
        """A user's id is their ka_id"""
        return self.ka_id


# todo: things like Comments that have properties like text_content which send
# off requests are for some reason being called when I use autocompletion in
# my python repl.  This is bad because the properties take a long time to be
# called and autocompletion results should be fast.  The properties can also
# raise errors, which is extra bad.  This is due to hasattr which checks to
# see if getattr raises an AttributeError, so I'm not sure if I can do much
# about it...
class Comment(abcs.Editable, abcs.Replyable, abcs.Deletable):
    """Any kind of comment on KA"""
    # these properties work no matter where the comment is
    api_delete = property(kaurl("api/internal/feedback/{.id}").format)
    api_reply = property(kaurl("api/internal/discussions/{.id}/replies").format)

    meta_path_map = {
        "text_content": ["content"]
    }

    def __init__(self, comment_id, context):
        self.comment_id = comment_id

    def get_reply_data(self):
        resp = requests.get(self.api_reply)
        resp.raise_for_status()
        yield from resp.json()

    def get_author(self):
        """Returns the ``User`` who wrote the comment."""
        return User(self.get_metadata()["authorKaid"])

    def get_parent(self):
        raise NotImplementedError

    def edit(self, session, message):
        session.put(self.api_edit,
            json={
                "text": message
                # topic?
            }
        ).raise_for_status()

    @property
    def id(self):
        """Comments use their comment_id for identication"""
        return self.comment_id


class ProgramComment(Comment):
    """A comment in the context of a KA program"""
    api_get = property(kaurl("api/internal/discussions/scratchpad/{0.program_id}/comments?qa_expand_key={0.id}").format)
    api_edit = property(kaurl("api/internal/discussions/scratchpad/{0.program_id}/comments/{0.id}").format)

    # ProgramCommentReply is not - and cannot be - implemented yet, so we
    # can't just set reply_type to ProgramCommentReply
    reply_type = property(lambda _: ProgramCommentReply)

    def __init__(self, ka_id, context):
        """Program comments take a ka_id, which is a long string KA uses to identify the comment.  \
        Usually, this is a string that starts with "kaencrypted_".  I believe that some other types of \
        comment ids work, although thanks to the undocumented nature of the internal api, \
        I would stick to the "kaencrypted_" ones.

        You also need a context object.  These are normally Program objects, but they can also be other \
        ProgramComment objects, or anything with a program_id"""
        super().__init__(ka_id, context)
        self.program_id = context.program_id

    def get_program(self):
        """Returns the ``Program`` that the comment was posted on."""
        return Program(self.program_id)

    get_parent = get_program

    def get_metadata(self):
        # when using qa_expand_key, the first comment will be the one we want,
        # so pop out the first comment
        return super().get_metadata()["feedback"].pop(0)

    @property
    def url(self):
        return "{}?qa_expand_key={}".format(self.get_program().url, self.id)
        

class ProgramCommentReply(ProgramComment):
    """A reply to a program comment"""
    def reply(self, session, message):
        """Adds a ``ProgramCommentReply`` to the thread.
        The reply will start with the character '@', followed by the author of this comment \
        to make it more clear what we are replying to.
        If you don't want this behavior, use ``reply.get_parent().reply`` instead."""
        return self.get_parent().reply(session, "@{metadata[authorNickname]}: {message}".format(
            metadata=self.get_metadata(), message=message
        ))

    def get_parent(self):
        """Returns the ``ProgramComment`` that started the thread."""
        return ProgramComment(super().get_metadata()["key"], self)

    def get_metadata(self):
        """Returns a dictionary with information about this ``ProgramCommentReply``."""
        # there's no way that I've found to get comment reply metadata directly, 
        # so we iterate though the comment thread until you find this comment
        for comment_data in self.get_parent().get_reply_data():
            if comment_data["key"] == self.id:
                return comment_data
        raise TypeError("{.id} does not identify a ProgramCommentReply".format(self))

        # I'm keeping this todo until I can fully address it, although I did
        # add an error

        # todo: raise some error instead of returning None.  What error?  IDK.
        # I'm almost tempted to pretend it's an HTTPError, but I'll need to do
        # some research into why we would get here (We can get here btw.
        # That's how I found this).  Would self.get_parent().get_reply_data()
        # raise an HTTPError if self.comment_key was nonsense?  If that's the
        # case, we will only (probably) be here if comment_key was a
        # ProgramComment key instead of a ProgramCommentReply key, so we would
        # probably want to have an error that's more specific (like TypeError
        # maybe?).  Man, there are so many edge cases with this stuff that I
        # really should look into now that I think about it...  We are also
        # probably going to need to keep a lot of this comment to explain why
        # we raise the error we do.

    def get_reply_data(self):
        """Yields all ``ProgramCommentReply``s that were posted after this one."""
        # Similar principle to get_metadata - we can't get what we want directly.
        gen = self.get_parent().get_reply_data()

        while next(gen)["key"] != self.id:
            pass

        yield from gen


# jinja2 is probably a good choice for Program formaters.  I might even want to add one to this class for convenience.
class Program(abcs.Editable, abcs.Replyable, abcs.Questionable, abcs.Spinoffable, abcs.Deletable):
    """
    Any kind of "program" on KA, such as one created using 
    https://www.khanacademy.org/computer-programming/new/pjs
    """
    api_get = api_edit = api_delete = property(kaurl("api/internal/scratchpads/{.id}").format)
    api_reply = property(kaurl("api/internal/discussions/scratchpad/{.id}/comments").format)
    api_create_program = kaurl("api/internal/scratchpads")
    reply_type = ProgramComment

    meta_path_map = {
        "image_url": ["revision", "imageUrl"],
        "url": ["url"],
        "code": ["revision", "code"],
        "width": ["width"],
        "height": ["height"],
        "title": ["title"],
        "kind": ["userAuthoredContentType"]
    }

    def __init__(self, program_id):
        """Programs are constructed using a program id.
        A program id is the last part of a program's url, so \
        https://www.khanacademy.org/computer-programming/ka-api-bot-test/4617827881975808 \
        has the program id 4617827881975808"""
        self.program_id = program_id

    @classmethod
    def create(cls):
        raise todo

    def get_reply_data(self, **params):
        resp = requests.get(self.api_reply,
            params=dict({
                "sort": 1,
                "subject": "all",
                "lang": "en",
                "limit": 10
            }, **params)
        )
        resp.raise_for_status()
        data = resp.json()

        yield from data["feedback"]
        if not data["isComplete"]: # There are more comments we haven't gotten to yet
            yield from self.get_reply_data(**dict(params, cursor=data["cursor"]))

    def get_metadata(self):
        metadata = super().get_metadata()
        # image_url isn't in the right place, so put it there
        return update_dict_path(metadata, self.meta_path_map["image_url"], metadata.get("imageUrl"))

    @property
    def id(self):
        """Programs use their program_id for identication"""
        return self.program_id