"""US Department of State travel advisory RSS, current feed not an archive."""
import release_runtime
import re, xml.etree.ElementTree as ET
from urllib.parse import urlparse
import requests
URL = 'https://travel.state.gov/_res/rss/TAsTWs.xml'
NOTE = 'U.S. Department of State advisories are written primarily for U.S. citizens. They are not a Chinese government travel advisory, objective safety guarantee, legal advice, or a substitute for current local and official destination guidance. Conditions may change rapidly. The country-level level may differ from advice for specific areas; review the full official entry. RSS is the feed returned at query time; publication date may be old, entries and coverage can change, and this is not a historical archive. Keyword is a case-insensitive substring of RSS title, not a standardized country code. No match does not prove safety.'

def search(keyword, limit=20, offset=0, include_description=False, session=None):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('keyword required')
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or (offset < 0):
        raise ValueError('invalid pagination')
    if type(include_description) is not bool:
        raise ValueError('include_description must be boolean')
    r = (session or requests).get(URL, timeout=35)
    r.raise_for_status()
    b = r.content
    if len(b) > 5000000 or b'<!DOCTYPE' in b.upper() or b'<!ENTITY' in b.upper():
        raise ValueError('unexpected RSS response')
    root = ET.fromstring(b)
    if root.tag != 'rss' or root.find('channel') is None:
        raise ValueError('invalid RSS document')
    ch = root.find('channel')
    items = ch.findall('item')
    if not items:
        raise ValueError('RSS feed has no recognizable entries')
    out = []
    for i in items:
        title = i.findtext('title')
        link = i.findtext('link')
        date = i.findtext('pubDate')
        if not title or not link or (not date):
            raise ValueError('incomplete RSS entry')
        p = urlparse(link)
        if p.scheme != 'https' or p.hostname != 'travel.state.gov':
            raise ValueError('unexpected RSS source link')
        if keyword.strip().casefold() not in title.casefold():
            continue
        m = re.search('\\bLevel\\s+([1-4])\\b', title, re.I)
        x = {'title': title, 'published_raw': date, 'link': link, 'title_level': int(m.group(1)) if m else None}
        if include_description:
            x['description_html_raw'] = i.findtext('description')
        out.append(x)
    return {'source': URL, 'channel_last_build_date_raw': ch.findtext('lastBuildDate'), 'total_feed_items': len(items), 'matching': len(out), 'offset': offset, 'limit': limit, 'items': out[offset:offset + limit], 'note': NOTE}
