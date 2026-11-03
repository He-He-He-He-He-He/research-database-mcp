"""The BMJ public recent-headline RSS; not a comprehensive research index."""
import release_runtime
import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
URL = 'https://www.bmj.com/rss/recent.xml'
R = '{http://purl.org/rss/1.0/}'
D = '{http://purl.org/dc/elements/1.1/}'
P = '{http://purl.org/rss/1.0/modules/prism/}'

def search(keyword='', offset=0, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100 or any((c in keyword for c in '\r\n')):
        raise ValueError('关键词须为不超过100字的单行文本')
    if type(offset) is not int or offset < 0 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('offset 或 limit 无效')
    try:
        res = requests.get(URL, timeout=25)
        res.raise_for_status()
        if len(res.content) > 4000000:
            raise ValueError('响应过大')
        root = ET.fromstring(res.content)
    except (requests.RequestException, ET.ParseError):
        raise RuntimeError('BMJ 订阅源不可用或格式异常') from None
    channel = root.find(R + 'channel')
    if channel is None or channel.findtext(R + 'title') != 'Latest headlines from BMJ':
        raise RuntimeError('BMJ 订阅源标题不符')
    rows = []
    items = root.findall(R + 'item')
    for node in items:

        def val(k):
            return ' '.join((node.findtext(k) or '').split())
        title = val(R + 'title')
        if not title:
            raise RuntimeError('BMJ 订阅条目缺少标题')
        u = urlsplit(val(R + 'link'))
        link = 'https://www.bmj.com' + u.path if u.scheme in ('http', 'https') and u.hostname == 'www.bmj.com' and u.path.startswith('/content/') and (not u.username) and (not u.password) else None
        item = {'title': title, 'authors_raw': [x.text.strip() for x in node.findall(D + 'creator') if x.text and x.text.strip()], 'date_raw': val(D + 'date'), 'section_raw': val(P + 'section'), 'subsection_raw': val(P + 'subsection1'), 'url': link}
        if keyword.casefold() in title.casefold():
            rows.append(item)
    return {'source': 'The BMJ official recent-headline RSS', 'feed_title': channel.findtext(R + 'title'), 'feed_records': len(items), 'keyword': keyword, 'matched': len(rows), 'offset': offset, 'limit': limit, 'items': rows[offset:offset + limit], 'note': '只对当前 RSS 标题本地筛选，混合新闻、讣告等类别，不代表研究论文全库或历史；链接规范为官方 HTTPS 并移除查询参数，日期与栏目保留原值。学校机构、订购及全文权限未核。'}
