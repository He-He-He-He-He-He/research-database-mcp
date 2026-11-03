"""UN Geneva public RSS feeds; current feed only, not archive search."""
import release_runtime
import xml.etree.ElementTree as ET
import requests
BASE = 'https://www.ungeneva.org/en/news-media/'
SLUG = {'all': 'press-items-list', 'releases': 'press-releases-list', 'meetings': 'meeting-summaries-list', 'conferences': 'press-conferences-list', 'briefings': 'briefings-list'}

def search(feed='all', keyword='', limit=10):
    if feed not in SLUG:
        raise ValueError('Unknown UN Geneva feed')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('Invalid keyword')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('Invalid limit')
    url = BASE + SLUG[feed] + '/rss.xml'
    with requests.get(url, timeout=30, stream=True, allow_redirects=False) as r:
        if r.is_redirect or not r.ok:
            raise RuntimeError('UN Geneva RSS returned HTTP ' + str(r.status_code))
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 2000000:
                raise RuntimeError('UN Geneva RSS exceeds 2 MB')
    root = ET.fromstring(raw)
    channel = root.find('channel')
    if root.tag != 'rss' or channel is None:
        raise RuntimeError('Unexpected UN Geneva RSS')
    entries = []
    for item in channel.findall('item'):
        data = {k: item.findtext(k) for k in ('title', 'link', 'description', 'pubDate', 'guid')}
        if keyword.casefold() not in ' '.join((str(data.get(k) or '') for k in ('title', 'description'))).casefold():
            continue
        data['title_is_placeholder'] = bool((data.get('title') or '').startswith('%AutoEntityLabel:'))
        entries.append(data)
    return {'source': 'United Nations Office at Geneva official RSS', 'source_info': 'https://www.ungeneva.org/en/news-media/rss', 'source_url': url, 'feed': feed, 'keyword': keyword, 'feed_items': len(channel.findall('item')), 'matched_in_feed': len(entries), 'returned': len(entries[:limit]), 'items': entries[:limit], 'note': '仅当前 RSS 返回项的标题和摘要本地筛选，不是新闻网站历史全库；源站可能返回自动标签占位标题或 HTML，原样保留并标记。通知、会议纪要与最终法律文件不同，应阅读原文核实。'}
