## What is this?

This is a lightweight project to collect and process PIF team snippets.  Every Monday morning, the current PIFs will receive an e-mail asking for updates or blockers -- anything that they want to share with the group.  Each PIF replies to the e-mail, and at the end of the day, a digest e-mail is sent out to the group.

To subscribe people on the team, admins (Dan and Michelle) subscribe people over email by sending Hermes a request. For example, to subscribe Gaj and Ashley, we send this to our messaging server via `admin@piffer-updates.appspotmail.com`:

```
Gaj Sunthara, sivagajen.suntharalingam@gsa.gov, pif, subscribe
Ashley Jablow, ashley.jablow@gsa.gov, pif, subscribe
```

Oops. Gaj needs to be an admin and Ashley wants to unsubscribe. No problem:

```
Gaj Sunthara, sivagajen.suntharalingam@gsa.gov, pif, subscribe, admin
Ashley Jablow, ashley.jablow@gsa.gov, pif, subscribe, pif, unsubscribe
```

The server sends back a confirmation email each time with a summary of subscriptions:

```
Your changes were saved:

Gaj Sunthara, sivagajen.suntharalingam@gsa.gov, pif, subscribe, admin
Ashley Jablow, ashley.jablow@gsa.gov, pif, subscribe, pif, unsubscribe
```

Note that this project supports multiple teams, so that as long as the cron jobs are appropriately specified, you can use this project for other teams.  So, for example, you can swap out `pif` in the admin e-mails for `18f` or whatever.

That's it. Pretty simple. 

## Developing

This project rides on the Google App Engine Python SDK runtime. After it's installed locally and on your path:

```bash
$ cd pif-update
$ dev_appserver.py --clear_datastore=true --show_mail_body=true .
```

Endpoints will be available at http://localhost:8080 and the admin console will be available at http://localhost:8000. 

You can send update and admin emails using the admin form at http://localhost:8000/mail. For update emails, the reply-to address must match the reply-to address in the update reminder email that gets sent. Watch the dev console for the address.

App Engine admins can manually invoke the `/cron/update` endpoint to send out update emails. Similarly they can invoke the `/cron/digest` endpoint to trigger the digest email. You can also hit `/cron/digest?test=true` to get an HTML response message with the digest.

A standard development progression follows:

1. Navigate to the Inbound Mail tab at `localhost:8000` and send an e-mail with an admin as the sender to `admin@piffer-updates.appspotmail.com` with a line resembling `dan,dan@hammer.com,pif,subscribe`.  Check that `dan` was added to the datastore by navigating to `localhost:8000/datastore?kind=Subscriber`.
2. In a separate tab, navigate to `http://localhost:8080/cron/update/pif`.  Copy the `Reply-to:` address in your console, which will look like `update+ahJkZXZ...` and paste it into the `To:` line at `localhost:8000/mail`.  In the from line, paste the subscriber e-mail, in this case `dan@hammer.com`.  In the message body, type an example update with each line preceded by `*`.  
3. Navigate to `localhost:8080/cron/digest/pif` to send the digest to the team (of only one person, currently).  The digest body will appear in the console.  

Push to production with `appcfg.py update --oauth2 .`, as long as you have permissions (granted by [**@danhammer**](https://github.com/danhammer)).
