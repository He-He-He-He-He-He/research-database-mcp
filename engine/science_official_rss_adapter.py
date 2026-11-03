"""Science official RSS snapshots, metadata only."""
import release_runtime
import subprocess, xml.etree.ElementTree as ET
FEEDS = {'first-release': ('https://feeds.science.org/rss/science-aop.xml', 'Science First Release'), 'mixed': ('https://feeds.science.org/rss/science.xml', 'Science'), 'advances': ('https://feeds.science.org/rss/science-advances.xml', 'AAAS: Science Advances: Table of Contents')}
FEEDS.update({'robotics': ('https://feeds.science.org/rss/science-robotics.xml', 'AAAS: Science Robotics: Table of Contents'), 'immunology': ('https://feeds.science.org/rss/science-immunology.xml', 'AAAS: Science Immunology: Table of Contents'), 'signaling': ('https://feeds.science.org/rss/science-signaling.xml', 'AAAS: Science Signaling: Table of Contents')})

def search(feed='first-release', keyword='', offset=0, limit=20):
    if feed not in FEEDS:
        raise ValueError('未验证 feed')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词无效')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('分页无效')
    url, expected = FEEDS[feed]
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '4000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Science RSS unavailable: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 4000000:
        raise ValueError('RSS too large')
    root = ET.fromstring(p.stdout)
    ch = root.find('channel')
    if ch is None or (ch.findtext('title') or '').strip() != expected:
        raise ValueError('RSS频道不匹配')
    source_items = ch.findall('item')
    results = []
    for x in source_items:
        val = lambda tag: ' '.join((x.findtext(tag) or '').split())
        row = {'title': val('title'), 'url': val('link'), 'guid': val('guid'), 'date': val('pubDate')}
        if row['title'] and keyword.casefold() in row['title'].casefold():
            results.append(row)
    return {'source': 'Science official RSS', 'source_url': url, 'feed_title': expected, 'feed_records': len(source_items), 'last_build_date': ch.findtext('lastBuildDate'), 'keyword': keyword, 'matches': len(results), 'offset': offset, 'limit': limit, 'items': results[offset:offset + limit], 'note': '仅当前RSS条目、标题本地匹配；mixed 混合新闻与研究，first-release 非历史全库；不证明浙大订购或全文权限，日期和类别须回原文核验。'}
