"""Public CAPMAS NADA study catalogue. Metadata is not publication availability evidence."""
import release_runtime
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://metadata.capmas.gov.eg/en/index.php/catalog'
NOTE = 'CAPMAS catalogue metadata only: search may match descriptions, not title alone. Study dates and catalogue creation/modification are not proof of PDF publication dates; downloads, data access, historical versions and terms must be checked individually.'

def _get(url, params=None, session=None):
    r = (session or requests).get(url, params=params, timeout=45)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('catalogue response too large')
    return BeautifulSoup(r.text, 'html.parser')

def _url(url, expected_id=None):
    p = urlparse(url or '')
    if p.scheme != 'https' or p.hostname != 'metadata.capmas.gov.eg':
        raise ValueError('unexpected catalogue URL')
    if expected_id is not None and (not re.fullmatch('/en/index\\.php/catalog/' + str(expected_id) + '/download/\\d+', p.path)):
        raise ValueError('download link does not match study')
    return url

def search(keyword, page=1, limit=15, session=None):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('keyword required (max 200 chars)')
    if type(page) is not int or page < 1 or page > 1000:
        raise ValueError('page must be 1..1000')
    if type(limit) is not int or not 1 <= limit <= 15:
        raise ValueError('limit must be 1..15')
    s = _get(BASE, {'sk': keyword.strip(), 'ps': 15, 'page': page}, session)
    container = s.select_one('#search-result-container')
    if not container:
        raise ValueError('catalogue response missing results container')
    rows = container.select('.survey-row')
    c = container.select_one('.search-count')
    if not c:
        if page == 1 and (not rows) and ('Your search did not match any studies held in the catalog.' in container.get_text(' ', strip=True)):
            return {'keyword': keyword, 'page': page, 'total': 0, 'items': [], 'note': NOTE}
        raise ValueError('catalogue count missing; cannot identify empty result')
    m = re.search('Showing\\s+(\\d+)\\s*[-–]\\s*(\\d+)\\s+of\\s+(\\d+)', c.get_text(' ', strip=True), re.I)
    if not m:
        raise ValueError('unrecognized catalogue count')
    start, end, total = map(int, m.groups())
    expected = (page - 1) * 15 + 1
    if start != expected or end < start or end > total or (len(rows) != end - start + 1) or (len(rows) > 15):
        raise ValueError('catalogue returned wrong or incomplete page')
    items = []
    for row in rows:
        a = row.select_one('.title a')
        href = _url(a.get('href') if a else None)
        m2 = re.fullmatch('/en/index\\.php/catalog/(\\d+)', urlparse(href).path)
        if not m2:
            raise ValueError('unexpected study link')
        val = row.select_one('.study-idno .wb-value')
        country = row.select_one('.study-country')
        producer = row.select_one('.study-by')
        title = a.get_text(' ', strip=True)
        if not title:
            raise ValueError('study title missing')
        items.append({'id': m2.group(1), 'title': title, 'url': href, 'study_id': val.get_text(' ', strip=True) if val else None, 'country_year_raw': country.get_text(' ', strip=True) if country else None, 'producer': producer.get_text(' ', strip=True) if producer else None})
    return {'keyword': keyword, 'page': page, 'page_size': 15, 'total': total, 'items': items[:limit], 'source_page_count': len(items), 'truncated': len(items) > limit, 'note': NOTE}

def related(study_id, session=None):
    sid = str(study_id)
    if not re.fullmatch('[1-9]\\d{0,7}', sid):
        raise ValueError('invalid study ID')
    s = _get(BASE + '/' + sid + '/related-materials', session=session)
    info = s.select_one('#dataset-metadata-info')
    if not info or info.get('data-id') != sid:
        raise ValueError('study identity mismatch')
    title = s.select_one('#dataset-title')
    resources = []
    for r in s.select('.resources .resource'):
        name = r.select_one('.resource-info')
        a = r.select_one('a.download')
        fields = {}
        for tr in r.select('.tbl-resource-info tr'):
            td = tr.select('td')
            if len(td) == 2 and td[0].get_text(' ', strip=True) != 'Download':
                fields[td[0].get_text(' ', strip=True)] = td[1].get_text(' ', strip=True)
        if not name or not a:
            raise ValueError('malformed resource')
        resources.append({'title': name.get_text(' ', strip=True), 'download_url': _url(a.get('href'), sid), 'format': a.get('data-extension'), 'filename': a.get('data-filename'), 'download_label': a.get_text(' ', strip=True), 'metadata': fields})
    if not title or not s.select_one('.resources'):
        raise ValueError('study resource page incomplete')
    stats = {}
    for st in s.select('.study-header-right-bar .stat'):
        label = st.select_one('.stat-label')
        value = st.select_one('.stat-value')
        if label and value:
            stats[label.get_text(' ', strip=True)] = value.get_text(' ', strip=True)
    return {'id': sid, 'title': title.get_text(' ', strip=True), 'study_id': info.get('data-idno'), 'catalogue_dates_raw': stats, 'resources': resources, 'note': NOTE}
