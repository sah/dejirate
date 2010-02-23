import urllib2
import json
import re

import gdata.projecthosting.client
import gdata.projecthosting.data
import gdata.gauth
import gdata.client
import gdata.data
import atom.http_core
import atom.core

import xmlbegone

USERNAME = '' # the google username of someone who can create tickets
PASSWORD = '' # and the corresponding password

# replace this URL with a recent JIRA search for all of the tickets
# you want to migrate
URL = "http://jira.openqa.org/sr/jira.issueviews:searchrequest-xml/temp/SearchRequest.xml?&pid=10030&pid=10190&pid=10160&pid=10070&pid=10121&pid=10100&resolution=-1&sorter/field=updated&sorter/order=DESC&tempMax=1000"

if os.path.isfile("sejira.json"):
    data = json.load(open("sejira.json", "rb"))
else:
    resp = urllib2.urlopen(URL).read()
    data = xmlbegone.loads(resp)
    open("sejira.json", "wb").write(json.dumps(data))


client = gdata.projecthosting.client.ProjectHostingClient()
client.client_login(
    USERNAME,
    PASSWORD,
    source='dejirate',
    service='code')

project = 'jira-to-google-code'

def html2text(html):
    li_re = re.compile(r'<li[^>]*>')
    html = li_re.sub('* ', html)
    for tag in ['br', 'p', 'ul', 'ol', 'li', 'div', 'span']:
        tag_re = re.compile(r'</?%s[^>]*>' % tag)
        html = tag_re.sub('', html)
    return html

print len(data['rss']['channel']['item'])
for i, item in enumerate(data['rss']['channel']['item']):
    link = item['link'].replace('j2ee.jira.seleniumhq.org:8080', 'jira.openqa.org')
    desc = "%s: %s\n" % (item['key']['_text'], link)
    desc += "Reported by: %s (%s)\n" % (item['reporter']['_text'],
                                        item['reporter']['username'])
    desc += "On: %s\n" % item['created']
    if item['assignee']['_text'] != 'Unassigned':
        desc += "Assigned to: %s (%s)\n" % (item['assignee']['_text'],
                                            item['assignee']['username'])
    desc += "\n" + html2text(item['description'])
    labels = ['jira']
    if 'component' in item:
        if isinstance(item['component'], str):
            labels.append(item['component'])
        else:
            print "weird component:", item['component']
    result = client.add_issue(
        project,
        item['title'],
        desc,
        USERNAME,
        labels=labels)

    comments = item.get('comments', {'comment': []})['comment']
    if isinstance(comments, dict):
        comments = [comments]
    for comment in comments:
        text = "By: %s\nOn: %s\n\n%s" % (comment['author'], comment['created'], comment['_text'])
        client.update_issue(
            project,
            result.get_id().rsplit('/', 1)[1],
            USERNAME,
            comment=html2text(text),
            ccs=[])
