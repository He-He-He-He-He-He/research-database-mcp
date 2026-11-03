"""NEJM official specialty RSS, metadata only."""
import release_runtime
import subprocess, urllib.parse, xml.etree.ElementTree as ET
FEEDS = {'cardiology': 'Cardiology', 'hematology-oncology': 'Hematology/Oncology', 'nephrology': 'Nephrology', 'pulmonary-critical-care': 'Pulmonary/Critical Care'}
FEEDS.update({'allergy-immunology': 'Allergy/Immunology', 'clinical-medicine': 'Clinical Medicine', 'dermatology': 'Dermatology', 'emergency-medicine': 'Emergency Medicine', 'endocrinology': 'Endocrinology', 'gastroenterology': 'Gastroenterology', 'genetics': 'Genetics', 'geriatrics-aging': 'Geriatrics/Aging', 'health-policy': 'Health Policy', 'infectious-disease': 'Infectious Disease', 'neurology-neurosurgery': 'Neurology/Neurosurgery', 'obstetrics-gynecology': 'Obstetrics/Gynecology', 'pediatrics': 'Pediatrics', 'psychiatry': 'Psychiatry', 'rheumatology': 'Rheumatology', 'surgery': 'Surgery'})
BASE = 'https://onesearch-rss.nejm.org/api/specialty/rss'
D = '{http://purl.org/dc/elements/1.1/}'

def search(specialty='hematology-oncology', keyword='', offset=0, limit=20):
    if specialty not in FEEDS:
        raise ValueError('未验证的专科')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词过长')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('分页无效')
    url = BASE + '?' + urllib.parse.urlencode({'context': 'nejm', 'specialty': specialty})
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '4000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('NEJM RSS unavailable: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 4000000:
        raise ValueError('RSS too large')
    root = ET.fromstring(p.stdout)
    ch = root.find('channel')
    if ch is None or FEEDS[specialty].casefold() not in (ch.findtext('title') or '').casefold():
        raise ValueError('RSS 标题与请求专科不符')
    source_items = ch.findall('item')
    items = []
    for x in source_items:
        value = lambda tag: (x.findtext(tag) or '').strip()
        row = {'title': value('title'), 'url': value('link'), 'guid': value('guid'), 'authors_raw': value(D + 'creator'), 'date': value(D + 'date')}
        if row['title'] and keyword.casefold() in (row['title'] + ' ' + row['authors_raw']).casefold():
            items.append(row)
    return {'source': 'NEJM official specialty RSS', 'source_url': url, 'specialty': specialty, 'feed_title': ch.findtext('title'), 'feed_records': len(source_items), 'keyword': keyword, 'matched': len(items), 'offset': offset, 'limit': limit, 'items': items[offset:offset + limit], 'note': '仅当次 RSS 返回条目，本地匹配标题和作者；不代表该专科完整历史、学校订购或全文。日期为源 dc:date，须回原文核对。'}
