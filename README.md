About
=====

Simple XMPP bot using the [SleekXMPP python library](http://sleekxmpp.com/).

Install and run
===============

You should use python2 since there is a bug with sleexmpp and dnspython in python3.

	$ virtualenv venv
	$ source venv/bin/activate
	$ pip install -r requirements.txt
	$ python mybot.py --jid username@chat.uio.no/mybot --room room@conference.chat.uio.no --nick mybot

