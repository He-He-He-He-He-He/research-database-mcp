"""Nature official current RSS metadata; includes news and articles."""
import release_runtime
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
URL = 'https://www.nature.com/nature.rss'
FEEDS = {'nature': ('nature', 'Nature'), 'human-behaviour': ('nathumbehav', 'Nature Human Behaviour'), 'medicine': ('nm', 'Nature Medicine'), 'climate-change': ('nclimate', 'Nature Climate Change'), 'communications': ('ncomms', 'Nature Communications')}
R = '{http://purl.org/rss/1.0/}'
D = '{http://purl.org/dc/elements/1.1/}'
P = '{http://prismstandard.org/namespaces/basic/2.0/}'
FEEDS.update({'food': ('natfood', 'Nature Food'), 'sustainability': ('natsustain', 'Nature Sustainability'), 'energy': ('nenergy', 'Nature Energy'), 'cities': ('natcities', 'Nature Cities'), 'water': ('natwater', 'Nature Water'), 'machine-intelligence': ('natmachintell', 'Nature Machine Intelligence'), 'biotechnology': ('nbt', 'Nature Biotechnology'), 'genetics': ('ng', 'Nature Genetics'), 'physics': ('nphys', 'Nature Physics')})
FEEDS.update({'humanities-social-sciences': ('palcomms', 'Humanities and Social Sciences Communications'), 'communications-psychology': ('commspsychol', 'Communications Psychology'), 'communications-earth-environment': ('commsenv', 'Communications Earth & Environment'), 'communications-medicine': ('commsmed', 'Communications Medicine'), 'communications-engineering': ('commseng', 'Communications Engineering'), 'science-of-learning': ('npjscilearn', 'npj Science of Learning')})

def search(keyword='', offset=0, limit=20, journal='nature'):
    if journal not in FEEDS:
        raise ValueError('未验证的期刊')
    code, expected = FEEDS[journal]
    if not isinstance(keyword, str) or len(keyword) > 100 or any((c in keyword for c in '\r\n')):
        raise ValueError('关键词须为不超过100字的单行文本')
    if type(offset) is not int or offset < 0 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('offset 或 limit 无效')
    try:
        res = requests.get('https://www.nature.com/' + code + '.rss', timeout=25)
        res.raise_for_status()
        if len(res.content) > 4000000:
            raise ValueError('响应过大')
        root = ET.fromstring(res.content)
    except (requests.RequestException, ET.ParseError):
        raise RuntimeError('Nature 订阅源不可用或格式异常') from None
    channel = root.find(R + 'channel')
    if channel is None or channel.findtext(R + 'title') != expected:
        raise RuntimeError('Nature 订阅源标题不符')
    rows = []
    items = root.findall(R + 'item')
    for node in items:

        def val(k):
            return ' '.join((node.findtext(k) or '').split())
        title = BeautifulSoup(val(R + 'title'), 'html.parser').get_text(' ', strip=True)
        if not title:
            raise RuntimeError('Nature 订阅条目缺少标题')
        u = urlsplit(val(R + 'link'))
        link = 'https://www.nature.com' + u.path if u.scheme == 'https' and u.hostname == 'www.nature.com' and u.path.startswith('/articles/') and (not u.username) and (not u.password) else None
        item = {'title': title, 'authors_raw': [x.text.strip() for x in node.findall(D + 'creator') if x.text and x.text.strip()], 'date_raw': val(D + 'date'), 'doi': val(P + 'doi'), 'url': link}
        if keyword.casefold() in title.casefold():
            rows.append(item)
    return {'source': 'Nature portfolio official current RSS', 'feed_title': expected, 'feed_records': len(items), 'keyword': keyword, 'matched': len(rows), 'offset': offset, 'limit': limit, 'items': rows[offset:offset + limit], 'note': '只对当前 RSS 标题本地筛选，含新闻和文章，不代表研究论文全库或历史；链接仅保留官方 HTTPS 文章路径并去除查询参数，日期保留原值。学校机构、订购及全文权限未核。'}
