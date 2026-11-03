"""Parse one Cairn search HTML response from stdin; never persist raw response."""
import release_runtime
import json, re, sys
from html.parser import HTMLParser

class Reader(HTMLParser):

    def __init__(self):
        super().__init__()
        self.main = 0
        self.depth = 0
        self.card = None
        self.carddepth = 0
        self.h3 = 0
        self.text = []
        self.items = []
        self.head = 0
        self.title = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.main += 1
        if not self.main:
            return
        if tag == 'h1':
            self.head = 1
        if self.card is None and tag == 'div' and ('shadow-halo-sm' in a.get('class', '').split()):
            self.card = {'title': '', 'url': None}
            self.carddepth = 1
        elif self.card is not None:
            if tag == 'div':
                self.carddepth += 1
        if self.card is not None:
            if tag == 'a' and self.card['url'] is None and a.get('aria-label') and a.get('href', '').startswith('https://shs.cairn.info/'):
                self.card['url'] = a['href']
            if tag == 'h3':
                self.h3 = 1

    def handle_endtag(self, tag):
        if not self.main:
            return
        if tag == 'h1':
            self.head = 0
        if tag == 'h3':
            self.h3 = 0
        if self.card is not None and tag == 'div':
            self.carddepth -= 1
            if self.carddepth == 0:
                self.card['title'] = ' '.join(self.card['title'].split())
                if self.card['title'] and self.card['url']:
                    self.items.append(self.card)
                self.card = None
        if tag == 'main':
            self.main -= 1

    def handle_data(self, data):
        if not self.main:
            return
        self.text.append(data)
        if self.head:
            self.title.append(data)
        if self.card is not None and self.h3:
            self.card['title'] += data
p = Reader()
p.feed(sys.stdin.read())
text = ' '.join(p.text)
m = re.search('(\\d[\\d\\s\\u202f]*)\\s+résultats?', text, re.I)
print(json.dumps({'heading': ' '.join(' '.join(p.title).split()), 'total': int(re.sub('\\s', '', m.group(1))) if m else None, 'items': p.items}, ensure_ascii=False))
