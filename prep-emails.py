"""
Prep subscription email from CSV with fields 'first', 'last', 'agency', and
'email'.  Saves a CSV that can be copied into the body of an email to
admin@piffer-updates.appspotmail.com in order to manage team snippet
subscriptions.
"""


def _process(line, team='pif', status='subscribe', bundle=True):
    """Accepts a line with {first},{last},{agency},{email} and returns a
    properly formatted string for subscription email."""
    first, last, agency, email = [x.strip() for x in line.split(',')]
    name = '%s %s' % (first, last)

    if bundle:
        team_bundler = {
            'Ashley Jablow': 'Ashley Jablow and David Naffis',
            'David Naffis': 'Ashley Jablow and David Naffis',
            'Christopher Daggett': 'Christopher Daggett and Ben Getson',
            'Ben Getson': 'Christopher Daggett and Ben Getson'
        }
        if name in team_bundler.keys():
            name = team_bundler[name]

    return '%s [%s],%s,%s,%s' % (name, agency, email, team, status)


def convert_csv(csv_path='subscribe.csv'):
    """Accepts a filepath string to the csv and prints out the text body for a
    subscription email."""
    with open(csv_path) as f:
        content = f.readlines()
    for l in content:
        print _process(l)
