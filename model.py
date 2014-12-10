"""This module contains the model."""

from google.appengine.ext import ndb


class Subscriber(ndb.Model):
    """Represents a single person subscribed to a team.

    The keyname is the mail+team.
    """
    name = ndb.StringProperty()
    mail = ndb.StringProperty()
    status = ndb.StringProperty()  # subscribe | unsubscribe
    role = ndb.StringProperty()  # admin | None
    team = ndb.StringProperty()  # e.g., GFW, POTICO

    @classmethod
    def get_or_insert(cls, **data):
        data['team'] = data['team'].lower()
        data['mail'] = data['mail'].lower()
        key_name = '%s+%s' % (data['mail'], data['team'])
        return super(Subscriber, cls).get_or_insert(key_name, **data)

    @classmethod
    def subscribed(cls, team):
        """Return all subsribers for supplied team."""
        return cls.query(
            cls.status == 'subscribe',
            cls.team == team.lower()
        ).fetch(100)


class SubscriberUpdate(ndb.Model):
    """Represents a subscriber update and used to create a digest email.

    The keyname is mail+date+team"""
    name = ndb.StringProperty()  # Subsriber name
    mail = ndb.StringProperty()  # Subscriber mail
    team = ndb.StringProperty()  # The WRI team name
    message = ndb.TextProperty()
    date = ndb.DateTimeProperty()
    sent = ndb.BooleanProperty()  # True if update email sent
    error = ndb.StringProperty()  # The mail error if one occurred

    @classmethod
    def get_or_insert(cls, name, mail, team, date):
        key_name = '%s+%s+%s' % (team, mail, date.isoformat())
        return super(SubscriberUpdate, cls).get_or_insert(
            key_name, name=name, mail=mail, team=team.lower(), date=date)

    @classmethod
    def get_updates(cls, date, team):
        """Get SubscriberUpdate models for supplied date and team."""
        return cls.query(
            cls.date == date,
            cls.team == team.lower()
        ).order(-cls.name).fetch(100)


class Update(ndb.Model):
    """Represents an update event for a team and date."""
    date = ndb.DateTimeProperty()
    digest_sent = ndb.BooleanProperty(default=False)
    updates_sent = ndb.BooleanProperty(default=False)
    team = ndb.StringProperty()  # The WRI team name

    @classmethod
    def get_or_insert(cls, team, date):
        key_name = '%s+%s' % (team, date.isoformat())
        return super(Update, cls).get_or_insert(
            key_name, team=team, date=date)

    @classmethod
    def latest(cls, team):
        """Returns the latest Update entity for a team."""
        return cls.query(
            cls.team == team.lower()
        ).order(-cls.date).get()


class SubscriberDigest(ndb.Model):
    """Ensures a subscriber received a digest email for a given Update date.

    The keyname is email+date+team.
    """
    mail = ndb.StringProperty()  # Subscriber email
    date = ndb.DateTimeProperty()  # The date of the Update
    team = ndb.StringProperty()  # The WRI team name
    sent = ndb.BooleanProperty(default=False)  # True if subscriber got digest
    error = ndb.StringProperty()  # The mail error if one occurred

    @classmethod
    def get_or_insert(cls, mail, team, date):
        key_name = '%s+%s+%s' % (team, mail, date.isoformat())
        return super(SubscriberDigest, cls).get_or_insert(
            key_name, mail=mail, team=team.lower(), date=date)
