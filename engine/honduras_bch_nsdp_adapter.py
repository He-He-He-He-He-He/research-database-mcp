"""Honduras Central Bank NSDP: discover official SDMX files and inspect bounded observations."""
import release_runtime
import argparse, json, re, subprocess, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
PAGE = 'https://www.bch.hn/estadisticas-y-publicaciones-economicas/sistema-general-de-divulgacion-de-datos-de-honduras/sistema-divulgacion-de-datos'
MAX = 5000000

class Links(HTMLParser):

    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.link = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = {'text': [], 'links': []}
        if tag == 'a' and self.row is not None:
            self.link = dict(attrs).get('href')

    def handle_data(self, data):
        if self.row is not None and data.strip():
            self.row['text'].append(data.strip())

    def handle_endtag(self, tag):
        if tag == 'a' and self.row is not None and self.link:
            self.row['links'].append(self.link)
            self.link = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None

def _fetch(u):
    p = release_runtime.run(['/usr/bin/curl', '-q', '--fail', '--silent', '--show-error', '--compressed', '--location', '--proto-redir', '=https', '--max-time', '30', '--max-filesize', str(MAX), u], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Honduras Central Bank NSDP request failed: curl ' + str(p.returncode))
    if len(p.stdout) > MAX:
        raise ValueError('response exceeds 5 MB')
    return p.stdout

def catalog():
    h = Links()
    h.feed(_fetch(PAGE).decode('utf-8', 'replace'))
    out = []
    for row in h.rows:
        for link in row['links']:
            u = urljoin(PAGE, link)
            parts = urlsplit(u)
            if parts.scheme == 'https' and parts.hostname == 'www.bch.hn' and parts.path.lower().endswith('.xml'):
                out.append({'description': ' '.join(row['text']), 'url': u, 'file': parts.path.rsplit('/', 1)[-1]})
    return {'source': PAGE, 'files': out, 'note': 'Only central bank HTTPS XML files linked on the official NSDP; underlying providers vary.'}

def observations(filename, start=None, end=None, limit=100):
    if not isinstance(filename, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,100}\\.xml', filename) or '..' in filename:
        raise ValueError('invalid filename')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('limit must be 1..500')
    for v in (start, end):
        if v is not None and (not isinstance(v, str) or not re.fullmatch('\\d{4}(?:-\\d{2})?', v)):
            raise ValueError('period format YYYY or YYYY-MM')
    lower = start if start is None or len(start) > 4 else start + '-00'
    upper = end if end is None or len(end) > 4 else end + '-99'
    if lower and upper and (lower > upper):
        raise ValueError('invalid period range')
    found = [x for x in catalog()['files'] if x['file'] == filename]
    if len(found) != 1:
        raise ValueError('file not found or ambiguous in current official NSDP page')
    u = found[0]['url']
    root = ET.fromstring(_fetch(u))
    out = []
    matched = 0
    for s in root.iter():
        if s.tag.split('}')[-1] != 'Series':
            continue
        for x in s:
            if x.tag.split('}')[-1] != 'Obs':
                continue
            t = x.attrib.get('TIME_PERIOD', '')
            if not re.match('^\\d{4}', t):
                continue
            if start and (t[:4] < start[:4] or (len(start) > 4 and (not re.fullmatch('\\d{4}-\\d{2}', t) or t < start))):
                continue
            if end and (t[:4] > end[:4] or (len(end) > 4 and (not re.fullmatch('\\d{4}-\\d{2}', t) or t > end))):
                continue
            matched += 1
            if len(out) < limit:
                out.append({'series': dict(s.attrib), 'observation': dict(x.attrib)})
    return {'source': u, 'description': found[0]['description'], 'matched': matched, 'returned': len(out), 'observations': out, 'note': 'Local time filtering; read original SDMX attributes and metadata. Some periods and sectors may be estimates or provisional. Limit applies after download.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('catalog')
    q = s.add_parser('data')
    q.add_argument('filename')
    q.add_argument('--start')
    q.add_argument('--end')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    try:
        print(json.dumps(catalog() if a.cmd == 'catalog' else observations(a.filename, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as e:
        p.exit(1, str(e) + '\n')
if __name__ == '__main__':
    main()
