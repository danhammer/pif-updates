"""
Prep subscription email from CSV with fields 'first', 'last', 'agency', and
'email'.  Saves a CSV that can be copied into the body of an email to
admin@piffer-updates.appspotmail.com in order to manage team snippet
subscriptions.
"""

l = 'Dan, Hammer, NASA, daniel.hammer@gsa.gov'


def _process(line, team='pif'):
    """Accepts a line with {first},{last},{agency},{email} and returns a
    properly formatted string for subscription email."""
    first, last, agency, email = [x.strip() for x in line.split(',')]
    return '%s %s [%s],%s,%s,unsubscribe' % (first, last, agency, email, team)


def convert_csv(csv_path='subscribe.csv'):
    """Accepts a filepath string to the csv and prints out the text body for a
    subscription email."""
    with open(csv_path) as f:
        content = f.readlines()
    for l in content:
        print _process(l)
