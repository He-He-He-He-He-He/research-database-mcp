"""Browse ZJU Wenku's public teacher-work catalogue by institution."""
import release_runtime
import re
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
BASE = 'http://csid.zju.edu.cn/zjuwk/'
URL = urljoin(BASE, 'book/teacher')

def validate_page(total, total_pages, page, records):
    if total < 0 or total_pages < 0 or (total > 0 and (total_pages != (total + 14) // 15 or page > total_pages)) or (len(records) != min(15, max(0, total - (page - 1) * 15))):
        raise ValueError('page count and parsed records do not match source total')

def browse(academy_id='', page=1, timeout=20):
    if not isinstance(academy_id, str) or (academy_id and (not re.fullmatch('[a-fA-F0-9]{32}', academy_id))):
        raise ValueError('academy_id must be empty or a 32-character hexadecimal ID')
    academy_id = academy_id.lower()
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('page must be an integer from 1 to 1000')
    r = requests.get(URL, params={'academyId': academy_id, 'pageNumber': page, 'pageSize': 15}, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    text = soup.get_text(' ', strip=True)
    p = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*页', text)
    total = re.search('共\\s*(\\d+)\\s*条记录', text)
    if not p or not total or int(p.group(1)) != page:
        raise ValueError('unable to verify requested page')
    academies = []
    for a in soup.select('a[href^="book/teacher?academyId="]'):
        name = a.get_text(' ', strip=True)
        ids = parse_qs(urlparse(a['href']).query).get('academyId', [])
        if name and len(ids) == 1 and re.fullmatch('[a-fA-F0-9]{32}', ids[0]):
            academies.append({'id': ids[0], 'name': name})
    records = []
    for li in soup.select('li'):
        a = li.select_one('a[href^="book/teacher/detail?"]')
        ps = li.select('p.f-toe')
        if not a or not ps:
            continue
        ids = parse_qs(urlparse(a['href']).query).get('id', [])
        fields = {}
        for el in ps:
            k, sep, val = el.get_text(' ', strip=True).partition('：')
            if sep and k in ('题名', '著者', '出版社'):
                fields[k] = val
        if len(ids) == 1 and re.fullmatch('[a-fA-F0-9]{32}', ids[0]) and fields.get('题名'):
            records.append({'id': ids[0], 'title': fields['题名'], 'author': fields.get('著者'), 'publisher': fields.get('出版社'), 'url': urljoin(BASE, 'book/teacher/detail?id=' + ids[0])})
    count = int(total.group(1))
    pages = int(p.group(2))
    validate_page(count, pages, page, records)
    return {'source': '浙大文库教师著作目录', 'academy_id': academy_id, 'page': page, 'total_pages': pages, 'total': count, 'academies': academies, 'records': records, 'note': '题录不代表全文可读；上游 HTTP，请勿提交敏感信息。'}
