"""Selected structured engineering design survey figures from MOHURD releases."""
import release_runtime
import re, subprocess, tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
PAGES = {2024: 'https://www.mohurd.gov.cn/gongkai/fdzdgknr/sjfb/tjxx/tjgb/art/2025/art_b18a7ff900e040d885ed2ab30e929033.html', 2025: 'https://www.mohurd.gov.cn/gongkai/fdzdgknr/sjfb/tjxx/'}
PATTERNS = {'surveyed_companies': '全国共有([0-9]+)个具有工程勘察设计资质的企业参加了统计', 'year_end_employees': '企业年末从业人员([0-9]+(?:\\.[0-9]+)?)万人', 'new_survey_contracts': '工程勘察新签合同额(?:合计)?([0-9]+(?:\\.[0-9]+)?)亿元', 'new_design_contracts': '工程设计新签合同额(?:合计)?([0-9]+(?:\\.[0-9]+)?)亿元', 'new_epc_contracts': '工程总承包新签合同额(?:合计)?([0-9]+(?:\\.[0-9]+)?)亿元', 'survey_revenue': '工程勘察收入([0-9]+(?:\\.[0-9]+)?)亿元', 'design_revenue': '工程设计收入([0-9]+(?:\\.[0-9]+)?)亿元', 'epc_revenue': '工程总承包收入([0-9]+(?:\\.[0-9]+)?)亿元', 'r_and_d_spending': '科技活动费用支出总额为([0-9]+(?:\\.[0-9]+)?)亿元'}

def catalog():
    return [{'year': year, 'source_page': url} for year, url in sorted(PAGES.items(), reverse=True)]

def _read(url, cap, redirected=False):
    with requests.get(url, timeout=(10, 35), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            if redirected:
                raise ValueError('multiple redirects')
            target = urljoin(url, r.headers.get('Location', ''))
            parsed = urlsplit(target)
            if parsed.scheme != 'https' or parsed.netloc != 'www.mohurd.gov.cn' or (not parsed.path.startswith('/cms_files/filemanager/')) or (not parsed.path.lower().endswith('.doc')):
                raise ValueError('unexpected redirect')
            return _read(target, cap, redirected=True)
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > cap:
                raise ValueError('file exceeds size limit')
        return bytes(b)

def report(year):
    if type(year) is not int or year not in PAGES:
        raise ValueError('only 2024 and 2025 are supported')
    page = PAGES[year]
    soup = BeautifulSoup(_read(page, 2000000), 'html.parser')
    title = f'{year}年全国工程勘察设计统计公报'
    links = []
    for a in soup.select('a[href]'):
        if a.get_text('', strip=True) != title:
            continue
        u = urljoin(page, a['href'])
        v = urlsplit(u)
        if v.scheme == 'https' and v.netloc == 'www.mohurd.gov.cn' and (v.path == '/api-gateway/jpaas-web-server/front/document/download'):
            links.append(u)
    links = list(dict.fromkeys(links))
    if len(links) != 1:
        raise ValueError('expected one matching official attachment')
    doc = _read(links[0], 2000000)
    if not doc.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('expected DOC attachment')
    with tempfile.TemporaryDirectory(prefix='mohurd-') as tmp:
        source = Path(tmp) / 'report.doc'
        out = Path(tmp) / 'report.txt'
        source.write_bytes(doc)
        release_runtime.run(['/usr/bin/textutil', '-convert', 'txt', '-output', str(out), str(source)], check=True, timeout=30, capture_output=True)
        text = out.read_text(encoding='utf-8')
    if title not in text:
        raise ValueError('attachment title does not match year')
    metrics = {}
    for key, pat in PATTERNS.items():
        matches = list(re.finditer(pat, text))
        if len(matches) == 1:
            m = matches[0]
            unit = '个' if key == 'surveyed_companies' else '万人' if key == 'year_end_employees' else '亿元'
            metrics[key] = {'value': m.group(1), 'unit': unit, 'source_excerpt': m.group(0)}
    if not metrics:
        raise ValueError('no unambiguous supported metrics')
    return {'source': '住房和城乡建设部', 'year': year, 'source_page': page, 'attachment_url': links[0], 'title': title, 'metrics': metrics, 'source_text': text, 'note': '统计对象为参加调查且具有相关资质的企业；缺失字段不作为零，阅读原文核对口径。'}
