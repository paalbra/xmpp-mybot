About
=====

Simple XMPP bot using the [SleekXMPP python library](http://sleekxmpp.com/).

Install and run
===============

    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ cat << EOF > mybot.ini
    > [mybot]
    > jid=username@chat.uio.no
    >
    > [room@conference.chat.uio.no]
    > resource=mybot
    > nick=mybot
    > EOF
    $ python mybot.py
