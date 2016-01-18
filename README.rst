=================================
KACPAW (formally known as KACSAW)
=================================

KACPAW makes it simple to perform user actions related to the KA Computer Programming platform using Python!



Example Usage
-------------

This example should give you some idea of how to use KACPAW

.. code-block:: python

    import kacpaw

    session = kacpaw.KASession(your_username, your_password)
    program = kacpaw.Program("4617827881975808") # khanacademy.org/cs/-/4617827881975808

    print("Hello, I'm", session.user.name)
    print("I'm about to create a comment on", program.url)

    my_reply = program.reply(session, "I'm using KACPAW!") # create a Tips & Thanks on the program
    
    print("I just said", repr(my_reply.text_content))

    my_reply.reply(session, "Hooray!") # respond to that Tips & Thanks.

Full documentation will be coming soon... er, um eventually...



Running Tests
-------------
1) Run ``py.test -sv`` in this directory.
    * To get all the tests to pass, set the environment variable ``KACPAW_TEST_PROGRAM_ID`` to a program you own.
    * Optionally, set ``KA_USERNAME`` and ``KA_PASSWORD`` to skip the login.
2) Be patient!  The tests might take some time because we need to send some requests to KA.



Links
-----
KACPAW
 * `Github <https://github.com/Potato42/kacpaw>`_

KACPAW uses `Python 3 <https://www.python.org/>`_ with the `requests module <https://pypi.python.org/pypi/requests>`_.  `pytest <https://pypi.python.org/pypi/pytest>`_ is used for testing.