"""This module processes incoming update emails."""

import logging
import webapp2

from google.appengine.ext import ndb
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

# Unused import required for ndb.Key
from model import SubscriberUpdate


class UpdateHandler(InboundMailHandler):
    """Handler for incoming update emails from subscribers."""

    @classmethod
    def get_update(cls, body):
        """Process body to update lines starting with *, return as string."""
        updates = body.split('*')
        cleaned = [x.strip('[\n ]').replace('\n', '') for x in updates]
        filtered = filter(lambda x: x != '', cleaned)
        message = '* ' + '\n* '.join(filtered)
        return message

    @classmethod
    def get_urlsafe(cls, address):
        """Return urlsafe string from supplied email address.

        Example: 'PIF <update+ag5kZXZ@piffer-updates.appspotmail.com>' would
        return ag5kZXZ as the urlsafe string.
        """
        if address.find('<') > -1:
            urlsafe = address.split('<')[1].split('+')[1].split('@')[0]
        else:
            urlsafe = address.split('+')[1].split('@')[0]
        return urlsafe

    @classmethod
    def process_update(cls, address, body):
        """Process update from supplied message.to address and body."""
        urlsafe = cls.get_urlsafe(address)
        if not urlsafe:
            logging.error('Unable to extract urlsafe from %s' % address)
            return
        subscriber_update = ndb.Key(urlsafe=urlsafe).get()
        subscriber_update.message = cls.get_update(body)
        subscriber_update.put()
        return subscriber_update

    def receive(self, message):
        """Updates SubscriberUpdate model message using urlsafe key from
        reply-to address and message contained in the mail body.
        """
        body = [b.decode() for t, b in message.bodies('text/plain')][0]
        self.process_update(message.to, body)

routes = [
    UpdateHandler.mapping(),
]

handlers = webapp2.WSGIApplication(routes, debug=True)
