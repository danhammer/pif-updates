
"""Unit test covereage."""

import datetime
import unittest

from google.appengine.ext import testbed

import admin
import cron
import model
import update


class TestModel(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def test_Subscriber(self):
        data = [dict(name='dan', mail='dan@hammer.com', team='pif',
                     status='subscribe', role='admin'),
                dict(name='aaron', mail='aaron@hammer.com', team='pif',
                     status='subscribe')]

        for x in data:
            model.Subscriber.get_or_insert(**x)

        self.assertEqual(2, len(model.Subscriber.subscribed('gfw')))


class TestUpdateHandler(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_update(self):
        bodies = {
            "*line1\n*line2\n*line3": "* line1\n* line2\n* line3",
            "*line1\r\n*line2\r\n*line3": "* line1\n* line2\n* line3",
            "*line1\r\n": "* line1",
            "*line1*line2 *line3": "* line1\n* line2\n* line3"}
        for body, expected in bodies.iteritems():
            message = update.UpdateHandler.get_update(body)
            self.assertEqual(message, expected)

    def test_get_urlsafe(self):
        f = update.UpdateHandler.get_urlsafe
        tests = {
            'PIFfer <update+ag5kZXZ@pif-update.appspotmail.com>': 'ag5kZXZ',
            '<update+ag5kZXZ@pif-update.appspotmail.com>': 'ag5kZXZ',
            'update+ag5kZXZ@pif-update.appspotmail.com': 'ag5kZXZ',
        }
        urlsafe = 'ag5kZXZ'
        for address, urlsafe in tests.iteritems():
            self.assertEqual(f(address), urlsafe)

    def test_process_update(self):
        f = update.UpdateHandler.process_update

        # Create SubscriberUpdate
        date = datetime.datetime.now()
        x = model.SubscriberUpdate.get_or_insert(
            'dan', 'dan@hammer.com', 'pif', date)
        urlsafe = x.key.urlsafe()
        address = 'PIF <update+%s@pif-update.appspotmail.com>' % urlsafe
        body = '* did nothing\n* met nobody'
        f(address, body)

        # Check that the update message made it
        key_name = '%s+%s+%s' % ('pif', 'dan@hammer.com', date.isoformat())
        x = model.SubscriberUpdate.get_by_id(key_name)
        self.assertIsNotNone(x)
        self.assertEqual(x.message, body)


class TestCronDigestHandler(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_update(self):
        f = cron.CronDigestHandler.get_update
        update = f(model.SubscriberUpdate(
            name='dan', mail='dan@hammer.com', message='* dude'))
        self.assertEqual(update, 'dan <dan@hammer.com>\n* dude\n\n')

    def test_get_digest_message(self):
        f = cron.CronDigestHandler.get_digest_message
        date = datetime.datetime.now()
        msg = f('pif', 'digest', date, 'dan@hammer.com')
        msg.send()
        messages = self.mail_stub.get_sent_messages(to='dan@hammer.com')
        self.assertEqual(1, len(messages))
        message = messages[0]
        self.assertEqual('dan@hammer.com', message.to)
        body = [b.decode() for t, b in message.bodies('text/plain')][0]
        self.assertEqual(body, 'digest')

    def test_get_subscriber_update(self):
        f = cron.CronDigestHandler.get_subscriber_updates
        date = datetime.datetime.now()
        x = model.SubscriberUpdate.get_or_insert(
            name='dan', team='pif', mail='dan@hammer.com', date=date)
        x.message = '* dude'
        x.put()

        x = model.SubscriberUpdate.get_or_insert(
            name='dan', team='pif', mail='dan@hammer.com', date=date)
        updates = f('pif', date)
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0].message, '* dude')

    def test_process_digest(self):
        f = cron.CronDigestHandler.process_digest

        # Test no latest update
        f('pif')
        self.assertIsNone(model.SubscriberDigest.query().get())
        self.assertEqual([], self.mail_stub.get_sent_messages(to='dan@hammer.com'))

        # Test has update but no subscribers
        date = datetime.datetime.now()
        model.Update.get_or_insert('pif', date)
        f('pif')
        self.assertIsNone(model.SubscriberDigest.query().get())
        self.assertEqual([], self.mail_stub.get_sent_messages(to='dan@hammer.com'))

        # Test has update and subscriber but no digest
        model.Subscriber.get_or_insert(
            name='dan', team='pif', mail='dan@hammer.com', status='subscribe')
        digest = f('pif', test=True)
        self.assertIsNone(model.SubscriberDigest.query().get())
        self.assertIs(digest, '')
        self.assertEqual([], self.mail_stub.get_sent_messages(to='dan@hammer.com'))

        # Test has update and subscriber and digest
        x = model.SubscriberUpdate.get_or_insert(
            name='dan', team='pif', mail='dan@hammer.com', date=date)
        x.message = '* dude'
        x.put()
        digest = f('pif')
        key_name = '%s+%s+%s' % ('pif', 'dan@hammer.com', date.isoformat())
        sd = model.SubscriberDigest.get_by_id(key_name)
        self.assertIsNotNone(sd)
        self.assertTrue(sd.sent)
        self.assertEqual(digest, 'dan <dan@hammer.com>\n* dude\n\n')
        self.assertNotEqual([], self.mail_stub.get_sent_messages(to='dan@hammer.com'))


class TestCronUpdateHandler(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_reply_address(self):
        f = cron.CronUpdateHandler.get_reply_address
        urlsafe = 'foo'
        expected = 'PIF <update+%s@pif-update.appspotmail.com>' % urlsafe
        self.assertEqual(expected, f(urlsafe))

    def test_get_update_message(self):
        f = cron.CronUpdateHandler.get_update_message
        team = 'pif'
        to = 'daniel.hammer@gsa.gov'
        sender = 'update+foo@pif-update.appspotmail.com'
        date = datetime.datetime.now()
        msg = f(team, to, sender, date)
        msg.send()
        messages = self.mail_stub.get_sent_messages(to='daniel.hammer@gsa.gov')
        self.assertEqual(1, len(messages))
        message = messages[0]
        self.assertEqual('daniel.hammer@gsa.gov', message.to)
        self.assertEqual(
            'update+foo@pif-update.appspotmail.com', message.sender)
        body = [b.decode() for t, b in message.bodies('text/plain')][0]
        self.assertIsNot(body, '')

    def test_process_subscriber_update(self):
        f = cron.CronUpdateHandler.process_subscriber_update
        data = dict(name='dan', mail='dan@hammer.com', team='pif',
                    status='subscribe', role='admin')
        sub = model.Subscriber.get_or_insert(**data)
        date = datetime.datetime.now()

        f(date, sub)

        key_name = '%s+%s+%s' % ('pif', 'dan@hammer.com', date.isoformat())
        subup = model.SubscriberUpdate.get_by_id(key_name)
        self.assertTrue(subup.sent)

        messages = self.mail_stub.get_sent_messages(to='dan@hammer.com')
        self.assertEqual(1, len(messages))
        message = messages[0]
        self.assertEqual('dan@hammer.com', message.to)
        expect = "Just reply with a few brief bullets starting with *"
        body = [b.decode() for t, b in message.bodies('text/plain')][0]
        self.assertEqual(expect, body)

    def test_process_update(self):
        f = cron.CronUpdateHandler.process_update
        data = [dict(name='dan', mail='dan@hammer.com', team='pif',
                     status='subscribe', role='admin'),
                dict(name='aaron', mail='aaron@hammer.com', team='pif',
                     status='subscribe')]
        date = datetime.datetime.now()
        for x in data:
            model.Subscriber.get_or_insert(**x)

        f('pif', date)
        subups = model.SubscriberUpdate.get_updates(date, 'pif')
        self.assertEqual(len(subups), 2)


class TestAdminHandler(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

        self.body = 'dan,dan@hammer.com,pif,subscribe,admin\n'
        self.body += '\naaron, aaron@hammer.com , pif, subscribe'

    def tearDown(self):
        self.testbed.deactivate()

    def test_is_admin(self):
        f = admin.AdminHandler.is_admin
        map(self.assertTrue,
            map(f, ['daniel.hammer@gsa.gov', 'michelle.hood@gsa.gov']))
        self.assertFalse(f('wannabe@admin.com'))

    def test_get_subscriptions(self):
        f = admin.AdminHandler.get_subscriptions
        subs = [x for x in f(self.body)]
        sub = dict(name='dan', mail='dan@hammer.com', team='pif',
                   status='subscribe', role='admin')
        self.assertIn(sub, subs)
        sub = dict(name='aaron', mail='aaron@hammer.com', team='pif',
                   status='subscribe')
        self.assertIn(sub, subs)
        self.assertTrue(len(subs) == 2)

    def test_update_subscriptions(self):
        f = admin.AdminHandler.update_subscription

        # Create new subscription
        data = dict(name='dan', mail='DAN@HAMMER.COM', team='PIF',
                    status='subscribe', role='admin')
        f(data)
        sub = model.Subscriber.get_by_id('dan@hammer.com+gfw')
        expected = dict(name='dan', mail='dan@hammer.com', team='pif',
                        status='subscribe', role='admin')
        self.assertDictContainsSubset(sub.to_dict(), expected)

        # Update existing subscription
        data = dict(name='DAN', mail='DAN@HAMMER.COM', team='PIF',
                    status='subscribe')
        f(data)
        sub = model.Subscriber.get_by_id('dan@hammer.com+gfw')
        expected = dict(name='dan', mail='dan@hammer.com', team='pif',
                        status='subscribe', role=None)
        self.assertDictContainsSubset(sub.to_dict(), expected)

if __name__ == '__main__':
    reload(update)
    reload(admin)
    reload(cron)
    reload(model)
    unittest.main(exit=False)
