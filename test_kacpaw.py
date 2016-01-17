# Tests for KACPAW

import pytest
from kacpaw import *


import os
import sys
from pprint import pprint
from functools import partial
from itertools import starmap
from operator import attrgetter, methodcaller


BOT_TEST_PROGRAM_ID = "4617827881975808"

USERNAME = os.environ["KA_USERNAME"]
PASSWORD = os.environ["KA_PASSWORD"] # no password for you!
PROGRAM_ID = os.environ.get("KACPAW_TEST_PROGRAM_ID", BOT_TEST_PROGRAM_ID)

program = Program(PROGRAM_ID) # this is a general-purpose program that you can set
bot_test_program = Program(BOT_TEST_PROGRAM_ID) # This is my KA API Bot Test program


@pytest.fixture(scope="session")
def session():
    return KASession(USERNAME, PASSWORD)

def test_bot_test_program():
    assert "Bot Test" in bot_test_program.title

    assert bot_test_program.url.startswith("https://www.khanacademy.org/computer-programming/")
    assert bot_test_program.url.endswith(bot_test_program.program_id)

    assert bot_test_program.kind == "pjs"

def test_edit_program(session):
    with open("README.rst") as readme:
        program.edit(session, 
            code="\n".join(map("// {}".format, readme.read().split("\n"))), # comment everything out
            image_url="https://www.python.org/static/community_logos/python-powered-h-140x182.png",
            title="KA API Bot Test",
            width=578, height=442
        )

def test_reply_reply(session):
    comment = ProgramComment("kaencrypted_24b83fe143a09cd4384ec150ada63106_e373eba7cb530161369280dafb3923a16c530c8502577f5cd77076d719034835297bf84dd112b0dedd7cab8a12cb330c3a79e942de63464de8e08406bfb973608db6dd102df955c24ca2055135520c4fa78b19cf4cb5ae3ee686238407a8f4dc4b5998d204edec504bb7aefeb212d97ef9c63438447765d160e376916fded96c818031d8b95ce1a2f4455cbebf07c65b4a897fdc4fef7a91743fcf15fce0d17ff64fc5118971423ee79e5c2df4c9556cc8196b96586c2ef6d9dd8831dd63554a", bot_test_program)

    reply = list(comment.get_replies())[-1] # most recent reply
    
    reply_text = "I just replied to a comment reply!  You said '{}'".format(reply.text_content)
    reply_reply = reply.reply(session, reply_text)

    assert reply_reply.text_content != reply_text # replying to a reply adds extra stuff to the beginning
    assert reply_reply.text_content.endswith(reply_text) # but they should end the same
    
    reply_reply.delete(session)
    with pytest.raises(requests.HTTPError):
        reply_reply.text_content

def test_comments(session):
    comment_text = "This is a temporary comment that will be deleted soon"
    comment = program.reply(session, comment_text)
    assert comment.text_content == comment_text

    reply_text = "I am yet another bot"
    reply = comment.reply(session, reply_text)
    assert reply.text_content == reply_text
    
    reply_text_addition = " ...who just edited a comment reply.  Seriously!  You can do that!"
    reply.edit(session, reply.text_content + reply_text_addition)
    assert reply.text_content == reply_text + reply_text_addition
    
    reply_text = "This comment reply is about to be deleted!"
    reply.edit(session, reply_text)
    assert reply.text_content == reply_text

    reply.delete(session)
    with pytest.raises(requests.HTTPError):
        reply.text_content

    comment_text = "This comment is about to be deleted!"
    comment.edit(session, comment_text)
    assert comment.text_content == comment_text

    comment.delete(session)
    with pytest.raises(requests.HTTPError):
        comment.text_content

def test_users():
    pass


#session.user.edit(session, name=session.user.name + " -- EDITED")




########## fun stuff ##########

# I'm sick of running into encoding errors trying to print people's names (Thanks, aidabaida and pamela!)
# so I made a few functions that deal with all the "fun" with encoding
def safe_str(val, encoding=sys.stdout.encoding, errors="xmlcharrefreplace"):
    """ 
    Handles encoding problems when converting val to a str in the encoding ``encoding``
    By default, characters that cannot be expressed with the encoding are replaced with 
    xml character escapes, but anything from docs.python.org/3/library/codecs.html#error-handlers
    will work.
    """
    return str(val)\
        .encode(encoding, errors=errors)\
        .decode(encoding, errors="ignore")

def safe_print(*args, **kwargs):
    """
    A print function that uses safe_str before printing.
    arguments:
        *args: same as print
        **kwargs: any optional kwargs from either print or safe_str
    """
    # split kwargs into two dictionaries, one with the keys ["encoding", "errors"]
    # to be passed into safe_str, and one with everything else, to be passed into print
    enc_kwds = {
        key: kwargs.pop(key) for key in dict(kwargs) 
            if key in ["encoding", "errors"]}

    print(*map(partial(safe_str, **enc_kwds), args), **kwargs)

def print_users(to_test=["tn1b12p", "aidabaida", "peterwcollingridge",
                        "pamela", "benburrill","charkittycat"]):
    for username in to_test:
        user = User.from_username(username)
        safe_print(user.name, "says:", user.bio)

if __name__ == "__main__":
    # if run as a script, print out some users for fun
    print_users()


#def callall(*funcs):
#    map(partial(map, methodcaller("__call__"), [attrgetter("__hash__"), attrgetter("__name__")]), [{},[],()])
#    def func(*args, **kwargs):
#        return map(methodcaller("__call__", *args, **kwargs), funcs)
#    return func

#list(starmap(safe_print, map(callall(attrgetter("text_content"), lambda reply: reply.get_metadata()["sumVotesIncremented"]), ProgramComment("kaencrypted_2d15c4abeb674970f00a51ae8ce9b52b_397e2475e401b794d5c12d2de18d7b2d3889d3441051d2a1df1f8bf55228b9d119dae1aa982c07e260ae5b8be680511c859654681ace8b467191de4a31f555af27dc6132bb0c186f068a8e79cf5631d6f263c4290e8e487aae071829966e792a74e1b4c2e8eaca5ddadd015a1e76dc37bf9102658b5df6c645597d0209918101ec6dedfb3b7e722e858130fd3ef3838268214f5fe03b0b3241a29339eaa048c05ad39599815075c96c629c86bd73518865d48519d24ef573ebb54cc1ad930bb0", Program("6600216945491968")).get_replies())))
#exit()

# ProgramComment("kaencrypted_5891d27f1da26001ee14d2f592c97724_980670c1e2a66f255f28143e65a81f72d1748bcf5e5e9429e453550066c27d02a0a1fc156fe39288071811f946d11f42ef41963d062e4ff28ec53438f949651b25e05fa19832c0aab52f03f2f0eb233af69912da35b1dcc6d42230d2d53aa0f34c35db3b52d33aeab3b0305c0a5f6bd9624b86800f583096b93e680371465e6f777b710af530f7a8a36d42ac4823bfda8c3166d32fcda34790fbc0e70ea2e51a6636484cdf81bb803f0ef4d3438953cc6b876b3b7ee565889adaa1a030e438c6", program).reply(session, "Secret message!").edit(session, "Quick question: In your notifications, do you see the words 'Secret message!' instead of this?")