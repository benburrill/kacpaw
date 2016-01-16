import requests
from .utils import raiser, method, get_dict_path, update_dict_path


# A property for use in abstract base classes that must be overridden or it
# will raise a NotImplementedError when accessed
abc_prop = property(raiser(NotImplementedError))


def _make_item_getter(cls, item_name):
    """
    Creates a property for getting ``item_name`` from the ``meta_path_map``.
    """
    @method(cls, item_name)
    def get_meta_item(self):
        return get_dict_path(self.get_metadata(), self.meta_path_map[item_name])
    
    # todo: beter auto-generated docstring for this
    get_meta_item.__doc__ = "Gets ``{item_name}`` from ``{cls.__name__}``".format(
        cls=cls, item_name=item_name
    )
    
    return property(get_meta_item)


# We use a metaclass instead of a simple class decorator because we want it to
# work with inheritance
class MetaPathMapClass(type):
    """
    Metaclass for classes with ``meta_path_map``s

    This uses the ``meta_path_map`` to create getters (using
    _make_item_getter) for each of ``meta_path_map`` items

    ``meta_path_map``s define convenient names for items deeply nested in the
    content's metadata.  For example, a ``Program``'s metadata structure looks
    something like ``{"revision": {"code": "..."}}``, so it's meta_path_map
    might include ``{"code": ["revision", "code"]}``.  See comments about dict
    paths in utils.py for more info.
    """
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        meta_path_map = cls.meta_path_map
        for item_name in meta_path_map:
            if not hasattr(cls, item_name):
                setattr(cls, item_name, _make_item_getter(cls, item_name))


class Content(metaclass=MetaPathMapClass):
    """A thing that can be accessed using the KA API"""
    id = api_get = abc_prop
    meta_path_map = {}

    def __init__(self): # Content is too abstract to be initialized
        raise NotImplementedError

    def __eq__(self, other):
        """Content objects are considered equal when their ids match"""
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    # Content should have data about it
    def get_metadata(self):
        """Gets the content's metadata as a dict"""
        resp = requests.get(self.api_get)
        resp.raise_for_status()

        # KA uses json to represent API structures
        return resp.json()


# todo: Votable?  Also some of these -able names sound kinda awkward.

class Editable(Content):
    """An interface for content on KA that can be edited"""
    api_edit = abc_prop
    # sometimes editing uses PUT, sometimes it uses POST, so lets let the
    # implementer decide
    api_edit_method = "PUT"

    def edit(self, session, **kwargs):
        """
        Modifies the content's metadata using ``meta_path_map`` keys passed in
        through ``kwargs``.

        This assumes that the data passed into the content's ``edit`` request
        is formatted similarily to the content's metadata.
        """
        metadata = self.get_metadata()

        for name, value in kwargs.items():
            update_dict_path(metadata, self.meta_path_map[name], value)

        session.request(
            self.api_edit_method, self.api_edit,
            json=metadata
        ).raise_for_status()


class Replyable(Content):
    """An interface for content on KA that can be replied to"""
    api_reply = reply_type = abc_prop

    def reply(self, session, message, topic="computer-programming"):
        """Forms a reply to this content, returning the reply content object"""
        resp = session.post(self.api_reply,
            json={
                "text": message,
                "topic_slug": topic
            }
        )
        resp.raise_for_status()
        return self.reply_type(resp.json()["key"], self)

    def get_reply_data(self):
        """Yields data about the replies to this content"""
        # replies work in different ways for different things, so this is not
        # implemented here However, get_reply_data SHOULD BE A GENERATOR.
        # Mostly, this is for consistency with  Program.get_reply_data, but we
        # use the fact that it is a generator in other places too.
        raise NotImplementedError

    def get_replies(self):
        """Yields content formed from get_reply_data"""
        for reply in self.get_reply_data():
            yield self.reply_type(reply["key"], self)


class Questionable(Content):
    """An interface for content on KA that can have questions asked about it"""
    api_question = question_type = abc_prop

    def ask_question(self, session, question):
        raise todo

    def get_questions(self):
        raise todo


class Spinoffable(Content):
    """An interface for content on KA that can be spun-off from"""
    api_spinoff = abc_prop

    def spinoff(self):
        raise todo

    def get_spinoffs(self):
        raise todo


class Deletable(Content):
    """An interface for content on KA that can be deleted"""
    api_delete = abc_prop

    def delete(self, session):
        """Deletes this content"""
        session.delete(self.api_delete).raise_for_status()