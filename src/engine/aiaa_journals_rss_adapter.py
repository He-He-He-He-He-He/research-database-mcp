"""AIAA official RSS article metadata; eight verified active journals."""
import release_runtime
import subprocess, urllib.parse, xml.etree.ElementTree as ET
FEEDS = {'aiaaj': 'AIAA Journal', 'jpp': 'Journal of Propulsion and Power', 'jat': 'Journal of Air Transportation', 'jais': 'Journal of Aerospace Information Systems', 'ja': 'Journal of Aircraft', 'jgcd': 'Journal of Guidance, Control, and Dynamics', 'jsr': 'Journal of Spacecraft and Rockets', 'jtht': 'Journal of Thermophysics and Heat Transfer'}
R = '{http://purl.org/rss/1.0/}'
D = '{http://purl.org/dc/elements/1.1/}'
P = '{http://prismstandard.org/namespaces/basic/2.0/}'

def search(journal='aiaaj', keyword='', offset=0, limit=20):
    if journal not in FEEDS:
        raise ValueError('未验证的期刊')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词无效')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('分页无效')
    url = 'https://arc.aiaa.org/action/showFeed?' + urllib.parse.urlencode({'type': 'etoc', 'feed': 'rss', 'jc': journal})
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '4000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('AIAA RSS unavailable: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 4000000:
        raise ValueError('RSS too large')
    root = ET.fromstring(p.stdout)
    ch = root.find(R + 'channel')
    if ch is None or FEEDS[journal].casefold() not in (ch.findtext(R + 'title') or '').casefold():
        raise ValueError('RSS 标题与期刊不符')
    source_items = root.findall(R + 'item')
    results = []
    for x in source_items:
        val = lambda tag: ' '.join((x.findtext(tag) or '').split())
        row = {'title': val(R + 'title'), 'url': val(R + 'link'), 'doi': val(D + 'identifier'), 'authors_raw': [v.text.strip() for v in x.findall(D + 'creator') if v.text and v.text.strip()], 'date': val(D + 'date'), 'volume': val(P + 'volume'), 'issue': val(P + 'number'), 'cover_date': val(P + 'coverDate'), 'rights': val(D + 'rights')}
        if row['title'] and keyword.casefold() in (row['title'] + ' ' + ' '.join(row['authors_raw'])).casefold():
            results.append(row)
    return {'source': 'AIAA official journal RSS', 'source_url': url, 'journal': FEEDS[journal], 'feed_title': ch.findtext(R + 'title'), 'feed_records': len(source_items), 'matches': len(results), 'keyword': keyword, 'offset': offset, 'limit': limit, 'items': results[offset:offset + limit], 'note': '仅当前RSS中题录，本地筛选标题和作者；非期刊全历史、浙大订购或全文授权。时间及逐条版权须回原文核对。'}
