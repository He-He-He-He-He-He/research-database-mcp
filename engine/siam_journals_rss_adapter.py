"""SIAM publisher's official article RSS catalogue and read-only feeds."""
import release_runtime
import subprocess, urllib.parse, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
BASE = 'https://epubs.siam.org'
INFO = BASE + '/feeds'
R = '{http://purl.org/rss/1.0/}'
D = '{http://purl.org/dc/elements/1.1/}'
P = '{http://prismstandard.org/namespaces/basic/2.0/}'

def _fetch(url):
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '4000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('SIAM source unavailable: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 4000000:
        raise ValueError('response too large')
    return p.stdout

def catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    soup = BeautifulSoup(_fetch(INFO), 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        url = urllib.parse.urljoin(BASE, a['href'])
        u = urllib.parse.urlsplit(url)
        q = urllib.parse.parse_qs(u.query)
        title = a.get_text(' ', strip=True)
        if u.scheme != 'https' or u.netloc != 'epubs.siam.org' or u.path != '/action/showFeed' or (q.get('type') != ['etoc']) or (q.get('feed') != ['rss']) or (len(q.get('jc', [])) != 1) or (not title):
            continue
        if keyword.casefold() in title.casefold():
            out.append({'title': title, 'code': q['jc'][0], 'url': url})
    if not out and (not keyword):
        raise RuntimeError('未识别官网 RSS 列表')
    return {'source': 'SIAM official RSS index', 'source_url': INFO, 'matches': len(out), 'items': out, 'note': '包含历史刊名，各频道能否访问需逐一验证；不代表学校订购。'}

def search(code, keyword='', offset=0, limit=20):
    if not isinstance(code, str) or not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('输入无效')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('分页无效')
    hit = [x for x in catalog()['items'] if x['code'] == code]
    if len(hit) != 1:
        raise ValueError('期刊代码未在官方目录中唯一匹配')
    root = ET.fromstring(_fetch(hit[0]['url']))
    ch = root.find(R + 'channel')
    if ch is None:
        raise ValueError('Unexpected RSS')
    source_items = root.findall(R + 'item')
    items = []
    for x in source_items:
        val = lambda tag: ' '.join((x.findtext(tag) or '').split())
        row = {'title': val(R + 'title'), 'url': val(R + 'link'), 'doi': val(D + 'identifier'), 'authors_raw': [v.text.strip() for v in x.findall(D + 'creator') if v.text and v.text.strip()], 'date': val(D + 'date'), 'volume': val(P + 'volume'), 'issue': val(P + 'number'), 'cover_date': val(P + 'coverDate'), 'rights': val(D + 'rights')}
        if row['title'] and keyword.casefold() in (row['title'] + ' ' + ' '.join(row['authors_raw'])).casefold():
            items.append(row)
    return {'source': 'SIAM journal official RSS', 'source_url': hit[0]['url'], 'catalog_title': hit[0]['title'], 'feed_title': ch.findtext(R + 'title'), 'feed_records': len(source_items), 'matches': len(items), 'keyword': keyword, 'offset': offset, 'limit': limit, 'items': items[offset:offset + limit], 'note': '仅当次RSS题录、标题及作者本地包含匹配，不代表历史全库、学校订购或全文权限。日期、许可须核原文。'}
