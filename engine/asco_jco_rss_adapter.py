"""ASCO official JCO RSS current table-of-contents metadata."""
import release_runtime
import re, subprocess, xml.etree.ElementTree as ET
URL = 'https://ascopubs.org/action/showFeed?type=etoc&feed=rss&jc=jco'
R = '{http://purl.org/rss/1.0/}'
D = '{http://purl.org/dc/elements/1.1/}'
P = '{http://prismstandard.org/namespaces/basic/2.0/}'

def search(keyword='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词须不超过200字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(offset, bool) or (not isinstance(offset, int)) or (offset < 0):
        raise ValueError('分页无效')
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '4000000', URL], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('ASCO RSS unavailable: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 4000000:
        raise ValueError('RSS exceeds 4 MB')
    root = ET.fromstring(p.stdout)
    channel = root.find(R + 'channel')
    if channel is None or channel.findtext(P + 'publicationName') != 'Journal of Clinical Oncology':
        raise ValueError('Unexpected RSS channel')
    items = []
    for x in root.findall(R + 'item'):
        val = lambda tag: (x.findtext(tag) or '').strip()
        title = val(R + 'title')
        link = val(R + 'link')
        doi = val(P + 'doi')
        if not title or not link:
            continue
        item = {'title': title, 'url': link, 'doi': doi, 'authors': [v.text.strip() for v in x.findall(D + 'creator') if v.text and v.text.strip()], 'category': val(D + 'type'), 'journal': val(P + 'publicationName'), 'volume': val(P + 'volume'), 'issue': val(P + 'number'), 'starting_page': val(P + 'startingPage'), 'ending_page': val(P + 'endingPage'), 'cover_date': val(P + 'coverDate'), 'rights': val(D + 'rights')}
        if keyword.casefold() in ' '.join([title] + item['authors'] + [item['category']]).casefold():
            items.append(item)
    return {'source': 'ASCO JCO official RSS', 'source_url': URL, 'feed_title': channel.findtext(R + 'title'), 'feed_records': len(root.findall(R + 'item')), 'keyword': keyword, 'matched': len(items), 'offset': offset, 'limit': limit, 'items': items[offset:offset + limit], 'note': '仅当前 RSS 中文章级题录，本地匹配标题、作者和类型；不是期刊全部历史、检索总数、浙大订购或全文权限。cover_date 为期刊封面日期，可能是未来日期，不等于发表日期。'}
