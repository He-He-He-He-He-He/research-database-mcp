"""CNIPA official provincial patent infringement administrative adjudication monthly data."""
import release_runtime
import hashlib, re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
INDEX = 'https://www.cnipa.gov.cn/col/col61/index.html'
ARCHIVE = {'2026-05': 'https://www.cnipa.gov.cn/art/2026/6/18/art_89_206827.html', '2026-06': 'https://www.cnipa.gov.cn/art/2026/7/16/art_89_207201.html', '2026-07': 'https://www.cnipa.gov.cn/art/2026/8/13/art_89_207706.html', '2026-08': 'https://www.cnipa.gov.cn/art/2026/9/17/art_89_208204.html', '2026-09': 'https://www.cnipa.gov.cn/art/2026/10/16/art_89_208616.html'}
PATTERN = re.compile('(\\d{4})年(\\d{1,2})月各省（区、市）专利侵权纠纷行政裁决案件数据统计')

def _fetch(url):
    with requests.get(url, stream=True, timeout=(10, 30), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 3000000:
                raise ValueError('response too large')
    return bytes(data)

def catalog():
    found = dict(ARCHIVE)
    errors = []
    try:
        soup = BeautifulSoup(_fetch(INDEX), 'html.parser')
        for a in soup.find_all('a', href=True):
            m = PATTERN.search(a.get_text(' ', strip=True))
            url = urljoin(INDEX, a['href'])
            p = urlsplit(url)
            if m and p.scheme == 'https' and (p.hostname == 'www.cnipa.gov.cn') and re.fullmatch('/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_89_\\d+\\.html', p.path):
                found[f'{m.group(1)}-{int(m.group(2)):02}'] = url
    except (requests.RequestException, ValueError) as e:
        errors.append(str(e))
    return {'source': '国家知识产权局专利侵权纠纷行政裁决案件统计', 'items': [{'month': k, 'url': v} for k, v in sorted(found.items())], 'index_url': INDEX, 'errors': errors, 'note': '含已核验2026年5–9月和官网数据首页当前展示的月份；并非完整历史目录。'}

def table(month, region=''):
    if not isinstance(month, str) or not re.fullmatch('\\d{4}-(0[1-9]|1[0-2])', month):
        raise ValueError('month format YYYY-MM')
    if not isinstance(region, str) or len(region) > 50:
        raise ValueError('invalid region')
    entries = {x['month']: x['url'] for x in catalog()['items']}
    if month not in entries:
        raise ValueError('month not in available catalog')
    raw = _fetch(entries[month])
    soup = BeautifulSoup(raw, 'html.parser')
    title = ' '.join(soup.stripped_strings)
    m = PATTERN.search(title)
    if not m or f'{m.group(1)}-{int(m.group(2)):02}' != month:
        raise ValueError('publication month mismatch')
    candidates = []
    for t in soup.find_all('table'):
        rows = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)] for tr in t.find_all('tr')]
        if len(rows) > 30 and rows[0] and ('知识产权管理部门' in rows[0][0]):
            candidates.append(rows)
    if len(candidates) != 1:
        raise ValueError('official table not uniquely recognized')
    rows = candidates[0]
    headers = [''.join(x.split()) for x in rows[0]]
    if len(headers) != 5 or len(rows) != 34 or (not rows[-1][0].startswith('合计')):
        raise ValueError('table layout changed')
    results = []
    for row in rows[1:]:
        clean = [''.join(x.split()) for x in row]
        if len(clean) != 5 or any((not re.fullmatch('\\d+', v) for v in clean[1:])):
            raise ValueError('unexpected table row')
        if region in clean[0]:
            results.append(dict(zip(headers, clean)))
    return {'source': '国家知识产权局', 'month': month, 'url': entries[month], 'source_sha256': hashlib.sha256(raw).hexdigest(), 'headers': headers, 'total_rows': len(rows) - 1, 'rows': results, 'note': '月份为行政裁决案件立案及结案数；同时列本月与当年1月至本月累计，不能把累计值相加。各省、兵团及合计以原表为准，并非法院判决或专利申请数量。'}
