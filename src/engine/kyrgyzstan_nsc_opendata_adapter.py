"""National Statistical Committee of Kyrgyz Republic: public open data JSON."""
import release_runtime
import argparse, json, re
from html.parser import HTMLParser
import requests
BASE = 'https://stat.gov.kg'

class Page(HTMLParser):

    def __init__(self):
        super().__init__()
        self.links = []
        self.link = None
        self.depth = 0
        self.heading = []

    def handle_starttag(self, tag, attrs):
        if tag == 'h1':
            self.depth += 1
        elif self.depth:
            self.depth += 1
        if tag == 'a':
            href = dict(attrs).get('href', '')
            if re.fullmatch('/en/opendata/category/\\d+/', href):
                self.link = [href, []]

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1
        if tag == 'a' and self.link:
            self.links.append({'path': self.link[0], 'name': ' '.join(' '.join(self.link[1]).split())})
            self.link = None

    def handle_data(self, data):
        if self.depth:
            self.heading.append(data)
        if self.link is not None:
            self.link[1].append(data)

def get(path):
    s = requests.Session()
    s.trust_env = False
    with s.get(BASE + path, timeout=35, stream=True) as r:
        r.raise_for_status()
        result = bytearray()
        for chunk in r.iter_content(65536):
            result.extend(chunk)
            if len(result) > 8000000:
                raise ValueError('Response exceeds 8 MB')
        r.encoding = 'utf-8'
        return bytes(result).decode('utf-8-sig')

def page(path):
    p = Page()
    p.feed(get(path))
    return p

def directory(category=None):
    path = '/en/opendata/' if category is None else f'/en/opendata/category/{category}/'
    p = page(path)
    seen = set()
    links = []
    for item in p.links:
        if item['path'] not in seen and item['name']:
            seen.add(item['path'])
            item['id'] = int(item['path'].split('/')[-2])
            links.append(item)
    return {'source': BASE + path, 'page_title': ' '.join(' '.join(p.heading).split()), 'categories': links, 'note': 'Links may include global navigation and parent categories; inspect the chosen category before treating it as a dataset.'}

def dataset(category):
    path = f'/en/opendata/category/{category}/'
    p = page(path)
    if not p.heading:
        raise ValueError('Dataset page has no title')
    data = json.loads(get(path + 'json'))
    return {'source': BASE + path + 'json', 'metadata_source': BASE + path, 'title_and_unit': ' '.join(' '.join(p.heading).split()), 'data': data, 'license': 'CC BY-NC-SA 4.0; source attribution required; see source page.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('catalog')
    a.add_argument('--category', type=int)
    a = s.add_parser('data')
    a.add_argument('category', type=int)
    args = p.parse_args()
    if args.category is not None and args.category <= 0:
        p.error('category must be positive')
    print(json.dumps(directory(args.category) if args.cmd == 'catalog' else dataset(args.category), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
