"""MOHURD 2025 survey bulletins on construction supervision and cost consulting."""
import release_runtime
import re, subprocess, tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
PAGE = 'https://www.mohurd.gov.cn/gongkai/fdzdgknr/sjfb/tjxx/'
TITLES = {'supervision': '2025年全国建设工程监理统计公报', 'cost': '2025年工程造价咨询统计公报'}
PATTERNS = {'supervision': {'companies': ('全国共有([0-9]+)个具有工程监理资质的企业参加了统计', '个'), 'employees': ('企业年末从业人员([0-9.]+)万人', '万人'), 'supervision_staff': ('工程监理人员([0-9.]+)万人', '万人'), 'supervision_contracts': ('承揽监理合同额([0-9.]+)亿元', '亿元'), 'supervision_revenue': ('全年监理收入([0-9.]+)亿元', '亿元')}, 'cost': {'companies': ('全国共有([0-9]+)家登记工程造价咨询业务的企业参加了统计', '家'), 'employees': ('参加统计的企业共有从业人员([0-9]+)人', '人'), 'cost_consulting_staff': ('工程造价咨询人员([0-9]+)人', '人'), 'overall_revenue': ('企业营业收入合计([0-9.]+)亿元', '亿元'), 'cost_consulting_revenue': ('(?<!境外)工程造价咨询业务收入([0-9.]+)亿元', '亿元'), 'overseas_consulting_revenue': ('境外工程咨询业务收入([0-9.]+)亿元', '亿元')}}

def catalog():
    return [{'kind': k, 'title': v, 'source_page': PAGE} for k, v in TITLES.items()]

def _get(url, redirected=False):
    with requests.get(url, timeout=(10, 35), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            if redirected:
                raise ValueError('multiple redirects')
            dest = urljoin(url, r.headers.get('Location', ''))
            u = urlsplit(dest)
            if u.scheme != 'https' or u.netloc != 'www.mohurd.gov.cn' or (not u.path.startswith('/cms_files/filemanager/')) or (not u.path.lower().endswith(('.doc', '.docx'))):
                raise ValueError('unexpected attachment redirect')
            return _get(dest, True)
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 2000000:
                raise ValueError('response too large')
        return bytes(data)

def report(kind):
    if kind not in TITLES:
        raise ValueError('kind must be supervision or cost')
    title = TITLES[kind]
    soup = BeautifulSoup(_get(PAGE), 'html.parser')
    urls = []
    for a in soup.select('a[href]'):
        if a.get_text('', strip=True) != title:
            continue
        url = urljoin(PAGE, a['href'])
        p = urlsplit(url)
        if p.scheme == 'https' and p.netloc == 'www.mohurd.gov.cn' and (p.path == '/api-gateway/jpaas-web-server/front/document/download'):
            urls.append(url)
    urls = list(dict.fromkeys(urls))
    if len(urls) != 1:
        raise ValueError('expected one matching official attachment')
    raw = _get(urls[0])
    suffix = '.doc' if raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')) else '.docx' if raw.startswith(b'PK\x03\x04') else None
    if suffix is None:
        raise ValueError('unrecognized Word attachment')
    with tempfile.TemporaryDirectory(prefix='mohurd-survey-') as tmp:
        src = Path(tmp) / ('report' + suffix)
        out = Path(tmp) / 'report.txt'
        src.write_bytes(raw)
        release_runtime.run(['/usr/bin/textutil', '-convert', 'txt', '-output', str(out), str(src)], check=True, timeout=30, capture_output=True)
        text = out.read_text(encoding='utf-8')
    if title not in text:
        raise ValueError('unexpected title')
    metrics = {}
    for key, (pattern, unit) in PATTERNS[kind].items():
        found = list(re.finditer(pattern, text))
        if len(found) == 1:
            m = found[0]
            metrics[key] = {'value': m.group(1), 'unit': unit, 'source_excerpt': m.group(0)}
    if not metrics:
        raise ValueError('no unambiguous metrics')
    return {'source': '住房和城乡建设部', 'kind': kind, 'title': title, 'source_page': PAGE, 'attachment_url': urls[0], 'metrics': metrics, 'source_text': text, 'note': '两个报告调查对象不同，不应简单相加；遗漏指标不视为零。'}
