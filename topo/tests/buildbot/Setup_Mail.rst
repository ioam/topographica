SETTING UP MAIL NOTIFICATIONS
=============================

This document links to images hosted on doozy in `/var/www/buildbot/screenshots`. Should this no longer be available, they should be stored elsewhere.

SMTP server
-----------

To set up a buildbot that sends mail notifications from some machine, it needs to be running a `message transfer agent <http://en.wikipedia.org/wiki/Message_transfer_agent>`_ in order to have a running SMTP server. Otherwise, attempts to send mail will result in the
following in Buildbot's `twistd.log`::

   2013-02-09 04:26:18+0000 [-]  step 'shell_4' complete: failure
   2013-02-09 04:26:18+0000 [-]  <Build full_build>: build finished
   2013-02-09 04:26:18+0000 [-] sending mail (868 bytes) to ['s0833773@sms.ed.ac.uk']
   2013-02-09 04:26:18+0000 [-] Starting factory <twisted.mail.smtp.ESMTPSenderFactory instance at 0x31dc488>
   2013-02-09 04:26:18+0000 [Uninitialized] SMTP Client retrying server. Retry: 5
   2013-02-09 04:26:18+0000 [Uninitialized] SMTP Client retrying server. Retry: 4
   2013-02-09 04:26:18+0000 [Uninitialized] SMTP Client retrying server. Retry: 3
   2013-02-09 04:26:18+0000 [Uninitialized] SMTP Client retrying server. Retry: 2
   2013-02-09 04:26:18+0000 [Uninitialized] SMTP Client retrying server. Retry: 1
   2013-02-09 04:26:18+0000 [Uninitialized] Unhandled error in Deferred:
   2013-02-09 04:26:18+0000 [Uninitialized] Unhandled Error
       Traceback (most recent call last):
       Failure: twisted.internet.error.ConnectionRefusedError: Connection was refused by other side: 111: Connection refused.

The most commonly used MTA for Linux is `Postfix <http://en.wikipedia.org/wiki/Postfix_%28software%29>`_ which is simple yet powerful. Install using
`sudo apt-get install postfix`, and then follow the on-screen instructions for configuring. `You may need to press Tab in order to access the buttons <http://serverfault.com/questions/21214/installing-postfix-hangs-at-postfix-configuration-screen>`_ .

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_01.PNG

Select the `Internet site` option to make SMTP mail go directly from the machine:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_02.PNG

The system mail name suggested by default is `mail.doozy.inf.ed.ac.uk` but that doesn't work. Instead, use the hostname itself:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_03.PNG

After configuration, the mail name can be checked by typing::

   $ cat /etc/mailname
   doozy.inf.ed.ac.uk

Specify the administrator account:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_04.PNG

Give the list of equivalent domains. Others will be suggested but may be malformed/invalid:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_05.PNG

Set the options on the remaining screens as follows:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_06.PNG

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_07.PNG

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_08.PNG

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_09.PNG

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/postfix_10.PNG

`See a more detailed guide <https://help.ubuntu.com/10.04/serverguide/postfix.html>`_ for configuring Postfix. The final configuration should look
like this::

   $ cat /etc/postfix/main.cf
   # See /usr/share/postfix/main.cf.dist for a commented, more complete version
   
   # Debian specific:  Specifying a file name will cause the first
   # line of that file to be used as the name.  The Debian default
   # is /etc/mailname.
   #myorigin = /etc/mailname
   
   smtpd_banner = $myhostname ESMTP $mail_name (Ubuntu)
   biff = no
   
   # appending .domain is the MUA's job.
   append_dot_mydomain = no
   
   # Uncomment the next line to generate "delayed mail" warnings
   #delay_warning_time = 4h
   
   readme_directory = no
   
   # TLS parameters
   smtpd_tls_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
   smtpd_tls_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
   smtpd_use_tls=yes
   smtpd_tls_session_cache_database = btree:${data_directory}/smtpd_scache
   smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache
   
   # See /usr/share/doc/postfix/TLS_README.gz in the postfix-doc package for
   # information on enabling SSL in the smtp client.
   
   myhostname = doozy.inf.ed.ac.uk
   alias_maps = hash:/etc/aliases
   alias_database = hash:/etc/aliases
   myorigin = /etc/mailname
   mydestination = doozy.inf.ed.ac.uk, localhost
   relayhost = internalmailrelay.ed.ac.uk
   mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
   mailbox_size_limit = 0
   recipient_delimiter = +
   inet_interfaces = all
   inet_protocols = all

SENDING MAIL OUTSIDE THE ED.AC.UK NETWORK
-----------------------------------------

As seen in the above configuration, a `relayhost` has been set. Without it, postfix will successfully work with buildbot but only for addresses
inside the network, e.g. `s1234567@sms.ed.ac.uk`. Attempting to directly send SMTP to outside addresses (e.g. a SourceForge mailing list) will fail
because both the Informatics and the University firewalls restrict outgoing SMTP.

A `relayhost` will redirect outgoing mail through the higher-level institution server to avoid the restrictions. In our case, it sould be set to
`internalmailrelay.ed.ac.uk`; see `Setting up systems that generate mail <http://www.ed.ac.uk/schools-departments/information-services/services/computing/comms-and-collab/email/mail-relay/machines>`_ .

USING A CUSTOM MESSAGE
----------------------

Buildbot's default message is informative enough (see samples in the mailing list); however, a custom one can be defined if necessary.
See `MailNotifier in the manual <http://docs.buildbot.net/0.8.7p1/manual/cfg-statustargets.html#mailnotifier>`_.